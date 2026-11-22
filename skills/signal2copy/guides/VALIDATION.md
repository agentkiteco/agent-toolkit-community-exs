# Signal2Copy 1.2.0 validation

The package covers staged development, the retained synthetic deployment track and one independently verified local Exness demo lifecycle. It includes an English walkthrough for each role. The assembled app was also deployed to an isolated Cloudflare Worker in native read-only mode.

| Check | Observed outcome |
| --- | --- |
| Isolated demo setup | Exness identified both selected accounts as demo and flat. The accounts were outside existing copying. The isolated partner filter was off. Both app roles connected using retained access. |
| Real source lineage | The live opening deal omitted its order identifier. A bounded history lookup proved the exact opening deal and filled market order. |
| Exact 1:1 demo execution | A 0.01-lot market source position opened. Exness confirmed the investor copy at the same size. Stop managed the copied position and the provider test position was closed. An initial final snapshot returned HTTP 401. An independent read then confirmed zero positions and orders on both accounts. |
| Read efficiency and dispatch | In a 41-symbol fixture the direct quote required one condition read. Exact-lot sizing no longer requests an unused equity-currency rate. The final gate checks semantic position identity, current protection, transaction versions, fresh executable price, sizing and margin. New entries send only the protection prices that are set. |
| Regression | Generated tests exercised market order lineage, unknown result after restart and no resend, pending FX, pending edit, protection, owned Stop and report export. |
| Isolated Cloudflare | The image deployed in native read-only mode. Health, provider and investor authentication, retained account connections, one published strategy, account requirements and owner access were verified. After encrypted backup and app restart, the accounts, strategy and settings persisted. Start was denied and the app held zero trading intents. |

The live demo establishes one supported local market-copy path on Exness demo accounts. The cloud test establishes native onboarding and persistence in read-only mode. Live positive partner-only admission, cloud trading, the broader native lifecycle and real-money execution are outside this evidence. Use the isolated [provider guide](PROVIDER_GUIDE.md) and [investor guide](INVESTOR_GUIDE.md) with the project’s own controls and credentials.
