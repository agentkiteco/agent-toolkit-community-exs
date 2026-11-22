# Signal2Copy provider demo guide

Use your isolated Signal2Copy installation and a dedicated Exness demo account. Confirm with the investor that both test accounts are flat and outside existing copying. Your project’s BUILD_STATE lists the available modes and its app address.

1. Open the app and select **Register the provider** for a fresh installation or **Sign in** for an existing one. Use the installation invitation when registration asks for it. Enter your Partnership credentials privately in the app.
2. In **Source account**, enter the selected demo Trading account and its private credentials. Confirm observation consent and choose **Verify and connect source**. Check the returned account and currency.
3. Publish one test strategy. In **Account requirements**, review the partner filter. If enabled, the selected investor account must appear in the account-level Exness report. Use the saved provider key to verify access. A completed empty report blocks the selected account.
4. In **Native account reads**, connect streams for the agreed instrument. Wait until the operator has confirmed readiness for both roles and the investor has explicitly selected **Start copying**. The operator then places one minimum-size source demo position through the authorized broker path.
5. Confirm the investor’s final broker execution with the operator. After the investor selects **Stop**, the operator closes the exact test source position and reads both broker snapshots. Finish when both accounts show zero test positions and pending orders.

For the Cloudflare read-only walkthrough, perform the first three steps and verify restored connections after an owner-controlled restart. Start remains disabled in this mode.
