/// agent_escrow — trustless service escrow for the AI agent economy.
///
/// A buyer deposits SUI into an owned Escrow object. The seller can
/// release funds to themselves on delivery; the buyer can cancel otherwise.
module agent_escrow::escrow {
    use sui::coin::{Self, Coin};
    use sui::balance::{Self, Balance};
    use sui::event;
    use sui::object;
    use sui::sui::SUI;
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};

    /// One escrow deal. Owned by the buyer (they hold the receipt).
    public struct Escrow has key, store {
        id: UID,
        /// The locked funds.
        locked: Balance<SUI>,
        /// The only address allowed to release funds to itself.
        seller: address,
        /// Human/agent-readable label of what was purchased.
        service: vector<u8>,
    }

    /// Emitted when the seller releases the funds.
    public struct Released has copy, drop {
        escrow_id: ID,
        seller: address,
        amount: u64,
    }

    /// Emitted when the buyer cancels and reclaims.
    public struct Cancelled has copy, drop {
        escrow_id: ID,
        amount: u64,
    }

    /// Buyer creates an escrow locking `payment` for `seller`.
    public fun create(payment: Coin<SUI>, seller: address,
                      service: vector<u8>, ctx: &mut TxContext) {
        let buyer = tx_context::sender(ctx);
        let escrow = Escrow {
            id: object::new(ctx),
            locked: coin::into_balance(payment),
            seller,
            service,
        };
        event::emit(Created { escrow_id: object::uid_to_inner(&escrow.id), buyer, seller });
        transfer::public_transfer(escrow, buyer)
    }

    /// Emitted at creation.
    public struct Created has copy, drop {
        escrow_id: ID,
        buyer: address,
        seller: address,
    }

    /// Seller releases the locked funds to themselves.
    public fun release(escrow: Escrow, ctx: &mut TxContext) {
        let Escrow { id, locked, seller, service: _ } = escrow;
        let amount = sui::balance::value(&locked);
        event::emit(Released {
            escrow_id: object::uid_to_inner(&id),
            seller,
            amount,
        });
        transfer::public_transfer(coin::from_balance(locked, ctx), seller);
        object::delete(id);
    }

    /// Buyer cancels: funds return to them.
    public fun cancel(escrow: Escrow, ctx: &mut TxContext) {
        let Escrow { id, locked, seller: _, service: _ } = escrow;
        let amount = sui::balance::value(&locked);
        event::emit(Cancelled { escrow_id: object::uid_to_inner(&id), amount });
        transfer::public_transfer(coin::from_balance(locked, ctx),
                                  tx_context::sender(ctx));
        object::delete(id);
    }
}
