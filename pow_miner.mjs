#!/usr/bin/env node
/**
 * Headless PoWFaucet miner (sepolia-faucet.pk910.de).
 * Protocol reverse-engineered from pk910/PoWFaucet client source (Apache-2.0).
 *
 * Flow:
 *   POST /api/startSession {addr}            -> sessionId
 *   WSS  /ws/?session=<id>&cliver=2.5.0      -> "powParams" + nonce ranges
 *   argon2id(nonceHex(16) || preimageHex)    -> hash with N leading zero bits
 *   WS "foundShare" {nonce,data,params}      -> balance grows
 *   GET  /api/getSessionStatus?session=<id>  -> balance check
 *   POST /api/claimReward {}                 -> ETH payout to addr
 *
 * Usage: node pow_miner.mjs <eth_address> <max_seconds>
 */

import crypto from "crypto";
import fs from "fs";
import os from "os";
import path from "path";
import { createRequire } from "module";
import WebSocket from "ws";

const require = createRequire(import.meta.url);

const [, , ADDR, MAX_SECONDS = "600"] = process.argv;
if (!ADDR || !/^0x[0-9a-fA-F]{40}$/.test(ADDR)) {
  console.error("usage: node pow_miner.mjs <0x-address> [max_seconds]");
  process.exit(1);
}
const BASE = process.env.POW_FAUCET_URL || "https://sepolia-faucet.pk910.de";
const CLIVER = "2.5.0";
const deadline = Date.now() + parseInt(MAX_SECONDS, 10) * 1000;

// ---------- argon2 from the faucet repo (bundled wasm) ----------
// The repo file is CommonJS exporting getArgon2/getArgon2ReadyPromise.
// We fetch it at runtime so this script stays dependency-free otherwise.
let argon2Fn = null;
async function loadArgon2() {
  const candidates = [
    new URL("./libs/argon2_wasm.cjs", import.meta.url).pathname,
    "/tmp/PoWFaucet/libs/argon2_wasm.cjs",
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      const mod = require(path.resolve(p));
      await mod.getArgon2ReadyPromise();
      argon2Fn = mod.getArgon2();
      console.log("[miner] argon2 wasm loaded from", p);
      return;
    }
  }
  throw new Error("argon2_wasm.cjs not found");
}

// PoW params arrive as base64 JSON on the WS; difficulty = leading zero BITS.
function difficultyMask(difficulty) {
  const byteCount = Math.floor(difficulty / 8) + 1;
  const bitCount = difficulty - (byteCount - 1) * 8;
  const maxValue = Math.pow(2, 8 - bitCount);
  let mask = maxValue.toString(16);
  while (mask.length < byteCount * 2) mask = "0" + mask;
  return mask;
}

function powParamsStr(p, difficulty) {
  // matches utils/PoWParamsHelper.ts for ARGON2
  return `${p.a}|${p.t}|${p.v}|${p.i}|${p.m}|${p.p}|${p.l}|${difficulty}`;
}

function padNonce(nonce) {
  let nonceHex = nonce.toString(16);
  if (nonceHex.length < 16)
    nonceHex = "0000000000000000".substring(0, 16 - nonceHex.length) + nonceHex;
  return nonceHex;
}

function checkHash(nonce, preimageHex, params, dmask) {
  let nonceHex = nonce.toString(16);
  if (nonceHex.length < 16)
    nonceHex = "0000000000000000".substring(0, 16 - nonceHex.length) + nonceHex;
  // worker-argon2.ts: argon2(nonceHex, preimgHex, l, i, m, p, t, v)
  const hash = argon2Fn(nonceHex, preimageHex, params.l, params.i, params.m,
                        params.p, params.t, params.v);
  return hash.substring(0, dmask.length) <= dmask ? hash : null;
}

// ---------- HTTP helpers ----------
async function api(endpoint, method = "GET", body) {
  const rsp = await fetch(BASE + "/api/" + endpoint, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  return rsp.json();
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------- main ----------
(async () => {
  await loadArgon2();

  const cfg = await api("getFaucetConfig?cliver=" + CLIVER);
  console.log("[miner] faucet config ok, time offset:", cfg.time);

  // PoW params live in the faucet config: modules.pow
  const powCfg = cfg.modules?.pow;
  if (!powCfg) { console.error("[miner] no pow module in config"); process.exit(2); }
  const powParams = powCfg.powParams || powCfg.params; // {a,t,v,i,m,p,l}
  const difficulty = powCfg.powDifficulty ?? powCfg.difficulty;
  console.log("[miner] instance:", BASE);
  console.log("[miner] powParams:", JSON.stringify(powParams),
              "difficulty:", difficulty);

  const start = await api("startSession?cliver=" + CLIVER, "POST", { addr: ADDR });
  if (!start.session || start.status === "failed") {
    console.error("[miner] session failed:", JSON.stringify(start));
    process.exit(2);
  }
  console.log("[miner] session started:", start.session,
              "balance:", start.balance, "wei");

  // preimage comes with the startSession response (processSessionInfo):
  // modules.pow = { lastNonce, preImage, shareCount }
  const preimageB64 = start.modules?.pow?.preImage;
  if (!preimageB64) {
    console.error("[miner] no preimage in session info:",
                  JSON.stringify(start).slice(0, 300));
    process.exit(2);
  }
  const preimageHex = Buffer.from(preimageB64, "base64").toString("hex");
  console.log("[miner] preimage acquired:", preimageB64);

  // connect mining websocket (endpoint: /ws/pow per PoWModule.ts)
  const wsUrl = BASE.replace("https://", "wss://") +
    "/ws/pow?session=" + start.session + "&cliver=" + CLIVER;
  const ws = new WebSocket(wsUrl, {
    headers: { "Origin": BASE },
  });
  let reqId = 1;
  const pending = {};
  const sendReq = (action, data) => new Promise((resolve, reject) => {
    const id = reqId++;
    pending[id] = { resolve, reject };
    ws.send(JSON.stringify({ id, action, ...(data !== undefined ? { data } : {}) }));
  });

  let lastNonce = 0, sharesFound = 0, sharesAccepted = 0;

  ws.on("message", async (raw) => {
    const msg = JSON.parse(raw.toString());
    if (msg.rsp !== undefined) {
      const p = pending[msg.rsp];
      delete pending[msg.rsp];
      if (typeof p === "function") {
        p(msg.action !== "error" ? Promise.resolve(msg.data)
                                 : Promise.reject(msg.data));
      }
      // unsolicited responses (e.g. foundShare acks) are fine to ignore
      return;
    }
    switch (msg.action) {
      case "verify":
        // respond to random share verification
        try {
          const preimg = Buffer.from(msg.data.preimage, "base64").toString("hex");
          const hash = argon2Fn(padNonce(msg.data.nonce), preimg,
                                powParams.l, powParams.i, powParams.m,
                                powParams.p, powParams.t, powParams.v);
          await sendReq("verifyResult", {
            shareId: msg.data.shareId,
            params: powParamsStr(powParams, difficulty),
            isValid: !!hash,
          });
          sharesAccepted++;
        } catch (e) { console.error("[miner] verify error", e); }
        break;
      case "updateBalance":
        console.log("[miner] balance update:", msg.data.balance, "wei",
                    "(" + msg.data.reason + ")");
        break;
      case "killSession":
        console.log("[miner] session killed by server:", JSON.stringify(msg.data));
        process.exit(3);
    }
  });
  ws.on("open", () => console.log("[miner] ws open"));
  ws.on("error", (e) => console.error("[miner] ws error", e.message));

  await new Promise((r) => ws.on("open", r));

  // mine until deadline
  let minedHashes = 0;
  let statTime = Date.now();
  const dmask = difficultyMask(difficulty);
  const pstr = powParamsStr(powParams, difficulty);
  while (Date.now() < deadline) {
    // hash nonces for ~4s between status polls
    const burstEnd = Date.now() + 4000;
    while (Date.now() < burstEnd) {
      for (let i = 0; i < 8; i++) {
        const nonce = ++lastNonce;
        minedHashes++;
        const hash = checkHash(nonce, preimageHex, powParams, dmask);
        if (hash) {
          sharesFound++;
          console.log("[miner] SHARE FOUND nonce", nonce);
          sendReq("foundShare", {
            nonce, data: null, params: pstr, hashrate: 300,
          }).catch((e) => console.error("[miner] share rejected",
              e && e.code, e && e.message));
        }
      }
      await sleep(0); // yield
    }
    const rate = Math.round(minedHashes / ((Date.now() - statTime) / 1000));
    console.log(`[miner] hashes=${minedHashes} shares=${sharesFound} ` +
                `~${rate} H/s`);
  }

  // claim
  console.log("[miner] claiming…");
  const final = await api("getSessionStatus?session=" + start.session + "&details=1");
  console.log("[miner] final balance:", final.balance, "wei");
  if (BigInt(final.balance || "0") > 0n) {
    const claim = await api("claimReward", "POST", {});
    console.log("[miner] claim response:", JSON.stringify(claim).slice(0, 300));
  }

  try { sendReq("closeSession"); } catch {}
  console.log(`DONE mined_hashes=${minedHashes} shares=${sharesFound}`);
  process.exit(0);
})().catch((e) => { console.error("[miner] fatal", e); process.exit(1); });
