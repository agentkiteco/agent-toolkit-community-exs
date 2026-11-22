# Signal2Copy investor demo guide

Use the dedicated Exness demo account agreed for the isolated run. Confirm at the broker that it has zero positions and orders. Your project’s BUILD_STATE lists the app address and applicable mode.

1. Open the published test strategy and **Sign in** for your selected Trading account. Enter the credentials in the private app form. Choose **Connect account** and verify its number and currency.
2. If the provider has enabled the partner filter, the verified trading account must appear in the provider’s Exness account report. If blocked, ask the provider to check the account’s attribution.
3. In **Native account reads**, connect the instrument streams agreed with the operator. In **Copy settings**, select **1:1** and new trades only. Verify the summary and explicitly select **Start copying** once the operator confirms readiness. The lot count is copied exactly when the account’s volume and margin checks pass.
4. Wait for the operator’s single source demo position. Check the confirmed investor position and lots with the operator. The app’s subscription or request acknowledgement alone does not confirm a broker fill.
5. Select **Stop**. Confirm with the operator that the app stopped and the broker reports zero positions and orders. If the app shows **stopped_follow_up**, retain the evidence and let the operator reconcile that request before starting again.

For the Cloudflare read-only walkthrough, verify sign-in, **Connect account** and retained account and strategy after restart. Start remains disabled.
