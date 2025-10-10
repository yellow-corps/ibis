import { WebSocket } from "ws";

import express from "express";

import {
  DeliveryMethod,
  LATEST_API_VERSION,
  WebhookHandler
} from "@shopify/shopify-api";
import { shopifyApp, WebhookHandlersParam } from "@shopify/shopify-app-express";

const shopify = shopifyApp({
  api: {
    hostName: `localhost:8080`,
    apiKey: process.env.SHOPIFY_CLIENT_ID,
    apiSecretKey: process.env.SHOPIFY_CLIENT_SECRET,
    scopes: ["read_orders"],
    apiVersion: LATEST_API_VERSION,
  },
  auth: {
    path: "/api/auth",
    callbackPath: "/api/auth/callback"
  },
  webhooks: {
    path: "/api/webhooks"
  }
});

async function callBot(topic: string, shop: string, body: string) {
  const bodyObj = JSON.parse(body);
  bodyObj.shop = shop;

  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      jsonrpc: "2.0",
      method: "SHOPIFY__WEBHOOK",
      params: [topic, bodyObj],
      id: crypto.randomUUID()
    });

    const ws = new WebSocket("ws://localhost:6133", { timeout: 5 });

    ws.onopen = () => {
      ws.send(payload);
    };

    ws.onmessage = (event) => {
      const response = JSON.parse(event.data.toString());
      if (response.error) {
        reject(
          `Discord Error: ${response.error.message} [${response.error.code}]`
        );
      } else {
        resolve(response.result);
      }
      ws.close();
    };

    ws.onerror = (error) => {
      reject(`WebSocket Error: ${error}`);
      ws.close();
    };

    // 60 second timeout
    const timeoutId = setTimeout(() => {
      if (ws.readyState !== ws.CLOSED) {
        reject("Timeout Error: 60 seconds timeout reached.");
        ws.close();
      }
    }, 60 * 1000);

    ws.onclose = () => {
      clearTimeout(timeoutId);
    };
  });
}

const defaultHandler: WebhookHandler = {
  deliveryMethod: DeliveryMethod.Http,
  callbackUrl: shopify.config.webhooks.path,
  async callback(topic, shop, body) {
    try {
      await callBot(topic, shop, body);
    } catch (error) {
      console.error(
        "[ibis-shopify/ERROR]", error.stack ?? error
      );
      throw error;
    }
  }
};

const webhookHandlers: WebhookHandlersParam = {
  ORDERS_CREATE: defaultHandler,
  ORDERS_UPDATED: defaultHandler,
  ORDERS_FULFILLED: defaultHandler,
  ORDERS_CANCELLED: defaultHandler
};

const app = express();

app.get(shopify.config.auth.path, shopify.auth.begin());
app.get(
  shopify.config.auth.callbackPath,
  shopify.auth.callback(),
  shopify.redirectToShopifyOrAppRoot()
);
app.post(
  shopify.config.webhooks.path,
  shopify.processWebhooks({ webhookHandlers: webhookHandlers })
);
app.use(express.json());
app.use(shopify.cspHeaders());

app.listen(8080);
