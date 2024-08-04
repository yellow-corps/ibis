import fs from "node:fs";
import process from "node:process";

if (!process.env.NGROK_DOMAIN) {
  throw new Error("NGROK_DOMAIN environment variable is not defined.");
}

if (!process.env.SHOPIFY_CLIENT_ID) {
  throw new Error("SHOPIFY_CLIENT_ID environment variable is not defined.");
}

const ibisConfig = new URL("../shopify.app.toml", import.meta.url);

const output = [
  `name = "ibis"`,
  `handle = "ibis-${process.env.SHOPIFY_CLIENT_ID}"`,
  `application_url = "http://localhost:8080/"`,
  `embedded = false`,
  `client_id = "${process.env.SHOPIFY_CLIENT_ID}"`,

  `[[webhooks.subscriptions]]`,
  `topics = [`,
  `  "orders/create",`,
  `  "orders/updated",`,
  `  "orders/fulfilled",`,
  `  "orders/cancelled",`,
  `]`,
  `  uri = "https://${process.env.NGROK_DOMAIN}/api/webhooks"`,

  `[build]`,
  `include_config_on_deploy = true`,

  `[auth]`,
  `redirect_urls = [ "http://localhost:8080/api/auth/callback" ]`,

  `[access_scopes]`,
  `scopes = "read_orders"`,

  `[webhooks]`,
  `api_version = "2024-07"`,

  `[pos]`,
  `embedded = false`
].join("\n");

fs.writeFileSync(ibisConfig, output, "utf-8");
