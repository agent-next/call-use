# NahaLabs regional telephony

`use-call-naha` is the NahaLabs fork of `call-use` and now has a regional telephony foundation for South Africa (ZA, `+27`) and Lesotho (LS, `+266`).

## Architecture

```text
Lead Machine / Sales OS
        |
        v
   call-use runtime
        |
        v
 Regional dialing policy
        |
        v
 TelephonyProvider
        |
        +--> Twilio SIP
        +--> SA/Lesotho SIP trunk
        +--> Asterisk / FreeSWITCH
        |
        v
       PSTN
```

## Important deployment boundary

Number validation does **not** create PSTN connectivity. A deployment still needs a carrier/SIP provider that legally supports the destination country and an owned or verified caller ID. The provider adapter should be selected per deployment rather than embedded into the core runtime.

## Supported destinations

- South Africa: `+27` E.164 numbers.
- Lesotho: `+266` E.164 numbers.

`call_use.phone` validates the regional destination and caller ID formats. `call_use.dialing_policy` maps destinations to their local timezone and provides configurable contact hours.

## Production controls to add before live campaigns

1. Consent / lawful-contact gate before origination.
2. Tenant and campaign rate limits.
3. Do-not-contact / opt-out suppression.
4. Verified caller-ID enforcement.
5. Call authorization and action receipts.
6. Recording/transcript disclosure and configurable retention.
7. Provider webhook ingestion and durable call state.
8. PostgreSQL call ledger and Redis queue/state for multi-worker deployments.
9. Country-specific carrier routing and health checks.
10. POPIA and applicable telecommunications/consumer-contact review before production use.

The default contact window in code is an operational safety default, not legal advice; configure it for the deployment's actual compliance requirements and recipient preferences.
