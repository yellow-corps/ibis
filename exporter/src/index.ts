import { spawnSync } from "node:child_process";
import crypto from "node:crypto";
import { createWriteStream } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import express from "express";
import archiver from "archiver";

const RED_TOKEN = process.env.RED_TOKEN;
if (!RED_TOKEN) {
  throw new Error("RED_TOKEN environment variable was not defined.");
}

async function extractChannel(
  channelId: string,
  output: string,
  format: "HtmlDark" | "PlainText",
  botName: string,
  timezone: string
): Promise<void> {
  const command = "/opt/app/DiscordChatExporter.Cli";
  const args = [
    "export",
    "--channel",
    channelId,
    "--format",
    format,
    "--output",
    output,
    "--include-threads",
    "all",
    ...(botName ? ["--filter", `~from:${botName}`] : []),
    ...(format === "HtmlDark" ? ["--media"] : [])
  ];

  const process = spawnSync(command, args, {
    encoding: "utf-8",
    env: {
      ...(timezone ? { TZ: timezone } : null),
      DISCORD_TOKEN: RED_TOKEN,
      FUCK_RUSSIA: "true"
    }
  });

  const commandInput = "$ " + [command, ...args].join(" ") + "\n";

  console.log(commandInput + process.stdout);

  if (process.error ?? process.stderr) {
    console.error(process.error ?? process.stderr);
  }

  if (process.status !== 0) {
    throw new Error(
      `Non-zero status code returned by exporter: ${process.status}.`
    );
  }
}

async function createTextFile(folder: string): Promise<string> {
  const textFile = `${folder}.txt`;
  const contents = [];

  for (const file of await fs.readdir(folder)) {
    contents.push(await fs.readFile(`${folder}/${file}`, "utf-8"));
  }

  await fs.writeFile(textFile, contents.join("\n"));

  return textFile;
}

async function createZipFile(folder: string): Promise<string> {
  const zipFile = `${folder}.zip`;
  let streamResolve: (value: string) => void;
  let streamReject: (reason: archiver.ArchiverError) => void;
  const promise = new Promise<string>((resolve, reject) => {
    streamResolve = resolve;
    streamReject = reject;
  });
  const output = createWriteStream(zipFile);
  output.on("close", () => streamResolve(zipFile));

  const archive = archiver("zip", { zlib: { level: 9 } });
  archive.on("warning", streamReject);
  archive.on("error", streamReject);

  archive.pipe(output);
  archive.directory(folder, false);
  archive.finalize();

  return promise;
}

const app = express();

app.get<{ channelId: string }, {}, {}, { botName?: string }>(
  "/channel/:channelId/txt",
  async (req, res) => {
    const tempFolder = path.join("/tmp", crypto.randomUUID());
    await fs.mkdir(tempFolder, { recursive: true });

    try {
      extractChannel(
        req.params.channelId,
        tempFolder,
        "PlainText",
        req.query.botName,
        <string>req.headers.tz
      );
    } catch (err) {
      return res.status(400).send(err);
    }

    let textFile: string;
    try {
      textFile = await createTextFile(tempFolder);
    } catch (err) {
      console.log(`Error while collating text files: ${err}`);
      return res.status(500).send(err);
    }

    return res.download(textFile, (err) => {
      if (err) {
        console.log(`Error while downloading ${textFile}: ${err}`);
        res.status(500).send(err);
      }
      fs.rm(tempFolder, { recursive: true, force: true });
      fs.rm(textFile, { force: true });
    });
  }
);

app.get<{ channelId: string }, {}, {}, { botName?: string }>(
  "/channel/:channelId/zip",
  async (req, res) => {
    const tempFolder = path.join("/tmp", crypto.randomUUID());
    await fs.mkdir(tempFolder, { recursive: true });

    try {
      extractChannel(
        req.params.channelId,
        tempFolder,
        "HtmlDark",
        req.query.botName,
        <string>req.headers.tz
      );
    } catch (err) {
      return res.status(400).send(err);
    }

    let zipFile: string;
    try {
      zipFile = await createZipFile(tempFolder);
    } catch (err) {
      console.log(`Error while zipping up files: ${err}`);
      return res.status(500).send(err);
    }

    return res.download(zipFile, (err) => {
      if (err) {
        console.log(`Error while downloading ${zipFile}: ${err}`);
        res.status(500).send(err);
      }
      fs.rm(tempFolder, { recursive: true, force: true });
      fs.rm(zipFile, { force: true });
    });
  }
);
app.use(express.json());

console.log("listening on port 8081");
app.listen(8081);
