# yc-hack

### Prehackathon planning
**Project**
TikTok for video games
Imagine webpage with white box in middle (game zone)
you can scroll up and it will show next generated game (will need to pregenerate the next game)

We use dev server on freestyle.sh
We use morph llm to make quick apply edits to the game page


**Attack Plan**
NOTES FOR CURSOR: when you are done with each step, stop and let me, the human, test before proceeding
1. make a repo that has a basic webpage with: (scroll calls a function that prints hello world), big white space in the middle of screen that is a seperate component that is easily editable by code, prompt button to play a specific game
2. setup morph and freestyle: setup freestyle server so we have a dev server. Setup up morph so we can prompt llm to make edits live. create a python script that can basically use the freestyle + morph to make edits to the live dev server in the white box (thats in react)
  a) first setup a freestyle dev server: (documentation below) and ensure we can read and write from it
  b) setup morph (documentation below)






the env contains: FREESTYLE_API_KEY, MORPH_API_KEY, ANTHROPIC_API_KEY

our P0 will not have any quick cache for the next game item
wow factor can be using favial ques to auto scroll or smth (?)


```
---
title: Run a Dev Server
description: Use a git repo and dev server to create a hot reload environment.
---

import { CodeBlock } from "fumadocs-ui/components/codeblock";
import { CodeTabs } from "../../../src/components/code-tabs";

Dev Servers are instant development and preview environments for your [Git Repositories](/git).

They come with everything you need to show a live preview to your users, while giving your agents the ability to work with the code.

Dev Servers on Freestyle Dev Servers:

- Automatically keep `npm run dev` alive â€” if it crashes we detect that and restart it.
- An [MCP](#model-context-protocol-mcp) server that makes connecting your agents to the dev server easy.
- A managed Git Identity for your dev server, so it can push/pull code from the repo.

Special Features:

- VSCode Web Interface accessible for human collaboration on dev servers.
- Chromium + Playwright setup for testing

Coming Soon:

- VSCode Server Interface to open Dev Servers in VSCode and Chromium
- VSCode Language Server Interface to run LSP commands (which the MCP will have access to)

## Creating a Dev Server

In order to create a dev server, you'll need a Git Repository to base it on.

<CodeTabs
 typescript={{
  title: "create-repo.ts",
  code: `

    import { FreestyleSandboxes } from "freestyle-sandboxes";

    const freestyle = new FreestyleSandboxes();


    const { repoId } = await freestyle.createGitRepository({
      name: "Test Repository",

      // This will make it easy for us to clone the repo during testing.
      // The repo won't be listed on any public registry, but anybody
      // with the uuid can clone it. You should disable this in production.
      public: true,

      source: {
        url: "https://github.com/freestyle-sh/freestyle-next",
        type: "git",
      },
    });

    console.log(\`Created repo with ID: \${repoId}\`);

`}}

python={{
title: "create-repo.py",
code: `

    import freestyle

    client = freestyle.Freestyle("YOUR_FREESTYLE_API_KEY")

    repo = client.create_repository(
      name="Test Repository from Python SDK",


      # This will make it easy for us to clone the repo during testing.
      # The repo won't be listed on any public registry, but anybody
      # with the uuid can clone it. You should disable this in production.
      public=True,
      source=freestyle.CreateRepoSource.from_dict(
          {
              "type": "git",
              "url": "https://github.com/freestyle-sh/freestyle-base-nextjs-shadcn",
          }
      ),
    )

    print(f"Created repo with ID: {repo.repo_id}")
    `

}}
/>

Then, you can request a dev server for the repo you just created.

<CodeTabs typescript={{
  title: "request-dev-server.ts",
  code: `

    import { FreestyleSandboxes } from "freestyle-sandboxes";

    const freestyle = new FreestyleSandboxes();

    const devServer = await freestyle.requestDevServer({ repoId });

    console.log(\`Dev Server URL: \${devServer.ephemeralUrl}\`);

`
}} python={{

title: "request-dev-server.py",
code: `

    import freestyle

    client = freestyle.Freestyle("YOUR_FREESTYLE_API_KEY")

    dev_server = client.request_dev_server(repo_id=repo.repo_id)

    print(f"Dev Server URL: {dev_server.ephemeral_url}")
    `

}} />

This will give you a dev server that is automatically running `npm run dev`. If you don't keep it alive, **it will shut itself down**.

## Working with Dev Servers

When you run a dev server, you get access to the following utilities:

<CodeTabs typescript={{
  title: "dev-server.ts",
  code: `
const {
    ephemeralUrl, // URL to the dev server, shows whatever server the dev server is running
    mcpEphemeralUrl, // URL to the MCP server, which lets your AI Agents interact with the dev server
    codeServerUrl, // URL to the VSCode Web Interface

    commitAndPush, // Function to commit and push whatever is on the dev server now to the repo
    fs, // File system interface to the dev server
    process, // Process interface to the dev server to run commands

    isNew, // Boolean indicating if the dev server was just created
    shutdown, // Shutdown handle to stop the dev server

} = await freestyle.requestDevServer({
repoId: repoId,
});
`}}

python={{
title: "dev-server.py",
code: `

    dev_server = client.request_dev_server(
        repo_id=repo.repo_id,
    )

    ephemeral_url = dev_server.ephemeral_url # URL to the dev server, shows whatever server the dev server is running
    mcp_ephemeral_url = dev_server.mcp_ephemeral_url # URL to the MCP server, which lets your AI Agents interact with the dev server
    code_server_url = dev_server.code_server_url # URL to the VSCode Web Interface

    commit_and_push = dev_server.commit_and_push # Function to commit and push whatever is on the dev server now to the repo
    fs = dev_server.fs # File system interface to the dev server
    process = dev_server.process # Process interface to the dev server to run commands

    is_new = dev_server.is_new # Boolean indicating if the dev server was just created
    shutdown = dev_server.shutdown # Shutdown handle to stop the dev server

`

}} />

## The URLs

Dev Servers provide a series of URLs that you can use to get different interfaces from the dev server. All these URLs are **ephemeral**, we do not guarantee that they will be available, or the same at any future point. In order to work with them, we recommend re-requesting the dev server every time you want to use them.

| URL               | Description                                                                                                                             |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `ephemeralUrl`    | This url displays whatever is on **port 3000** of the dev server, or a loading indicator until that shows up                            |
| `mcpEphemeralUrl` | This url is an MCP that lets your AI work with the dev server                                                                           |
| `codeServerUrl`   | This url opens a VSCode window in the browser that is inside the dev server, useful for letting you/your users collaborate with the AI. |

## The File System Interface

The dev server provides a file system interface that lets you read and write files in the dev server.

### Writing files

You can write files using the `fs`. The default encoding is utf-8, but you can specify another one (like `base64`) if you want to upload something like an image.

<CodeTabs typescript={{
  title: "write-file.ts",
  code: `

    await fs.writeFile("src/index.tsx", \`console.log("Hello World!");\`);

`}} python={{
title: "write-file.py",
code:`
fs.write_file("/test.txt", "Hello, Freestyle!")
`
}}/>

### Reading files

You can read files using the `fs`. The default encoding is utf-8, but you can specify another one (like `base64`) if you want to download something like an image.

<CodeTabs typescript={{
  title: "read-file.ts",
  code: `

    const content = await fs.readFile("src/index.tsx");

    console.log(content);

`}} python={{
title: "read-file.py",
code: `

    content = fs.read_file("src/index.tsx")

    print(content)

`}}

/>

### Listing files

You can list files in a directory using the `fs`. This is not a recursive listing, it only lists files in the specified directory. If you want to list files recursively, you'll want to use the `process` interface to run a command like `ls -R` or `find .`.

<CodeTabs typescript={{
  title: "list-files.ts",
  code: `

    const files = await fs.ls("src");

    console.log(files);

`}} python={{
title: "list-files.py",
code: `

    files = fs.ls("src")

    print(files)

`}}/>

## Executing Commands

You can execute any command on the dev server using the `process` interface.

<CodeTabs typescript={{
  title: "run-command.ts",
  code: `

    const { stdout, stderr } = await process.exec("npm run dev");

    console.log(stdout);
    console.error(stderr);

`}} python={{
title: "run-command.py",
code: `

    result = process.exec("npm run dev")

    print(result.stdout)
    print(result.stderr)

`}}/>

### Running background tasks

You can run background tasks using the `process.exec`, by passing a second argument `true` to the `exec` function. This will run the task in the background.

<CodeTabs typescript={{
  title: "run-background-command.ts",
  code: `

    await process.exec("npm run dev", true);
    // This will run in the background so you can continue doing other things

`}} python={{
title: "run-background-command.py",
code: `

    process.exec("npm run dev", background=True)
    # This will run in the background so you can continue doing other things

`}}/>

## Committing and Pushing Changes

You can commit and push changes to the repo using the `commitAndPush` function. This will commit all changes in the dev server and push them to the repo. The commit will go to the branch that the dev server is currently on, which is usually `main`.

<CodeTabs typescript={{
  title: "commit-and-push.ts",
  code: `
    await commitAndPush("Updated index.tsx");
`}} python={{
title: "commit-and-push.py",
code: `

    commit_and_push("Updated index.tsx")

`}}/>

>

## Using in NextJS

When building a web interface for your dev server, we provide a `FreestyleDevServer` component for NextJS. The component automatically keeps the dev server alive.

To use it, you'll first need to create a server action to handle the request. This action
will create a dev server for the repo if one isn't already running or return the
status if one is already running.

```tsx title="preview-actions.ts"
"use server";

import { freestyle } from "@/lib/freestyle";

export async function requestDevServer({ repoId }: { repoId: string }) {
  const { ephemeralUrl, devCommandRunning, installCommandRunning } =
    await freestyle.requestDevServer({ repoId });

  return { ephemeralUrl, devCommandRunning, installCommandRunning };
}
```

Then, you can use the `FreestyleDevServer` component in your NextJS app with the `requestDevServer` action you just created.

```tsx
import { FreestyleDevServer } from "freestyle-sandboxes/react/dev-server";
import { requestDevServer } from "./preview-actions";

export function Preview({ repoId }: { repoId: string }) {
  <FreestyleDevServer actions={{ requestDevServer }} repoId={repoId} />;
}
```

## Working in Parallel

You can clone the repo locally and try pushing to it. You should see the dev
server update in realtime. Note this will only work if you made the repo public,
otherwise, you'll need to create git credentials to access the repo. See the
[Git Documentation](/git) for more information.

```bash
git clone https://git.freestyle.sh/<repoId>
```

For production use in App Builders, we suggest using isomorphic-git to manage
git from serverless JavaScript environments.

```ts
import git from "isomorphic-git";
import fs from "fs";
import http from "isomorphic-git/http/node";

git.clone({
  fs,
  url: "https://git.freestyle.sh/<repoId>",
  singleBranch: true,
  depth: 1,
  http,
});
```

## Model Context Protocol (MCP)

MCP is a protocol for allowing AI agents to discover and use tools. Dev servers
automatically expose a set of tools for interacting with the file system and
other core operations such as installing npm modules, running commands, and
testing code. You can get the url for this server in the dev server response.

We provide the following tools by default:

- readFile: Read a file from the dev server
- writeFile: Write a file to the dev server
- editFile: Search and replace based file editing
- ls: List files in a directory
- exec: Execute a command on the dev server
- commitAndPush: Commit and push changes to the repo
- npmInstall: Install an npm module on the dev server
- npmLint: Lint the code on the dev server

Together, these tools make it easy to get your agents started on development. They do not handle everything, but we recommend the MCP as a good starting point for building your own tools.

## On Current Limitations

Dev Servers are primarily made to run **JavaScript/TypeScript Dev Servers**. When we start a dev server, we run `npm run dev` and expect it to start a server on port 3000. If you want to add more on startup, you can change the script in `npm run dev` to run whatever you want. We automatically keep track of the process and restart it if it crashes.

This approach makes it theoretically work with other languages, but in practice not well. We are actively working on improving this. For the best experience today, a good rule of thumb is, "Would this be a part of my npm run dev workflow locally?" If the answer is yes, then it will work well on a dev server. If not, let us know, we'd like to make it work better.
```



title: morph docs
# Apply Model

> Apply code changes with the highest accuracy and speed

# What is Fast Apply?

The Apply Model intelligently merges your original code with update snippets at **98% accuracy** and **4500+ tokens/second**.
Companies like Cursor use this method for fast, reliable edits.

Methods like search and replace face high error rates and are slower because they need to output negative tokens and positive tokens.
Unlike diff-based methods, it preserves code structure, comments, and syntax while understanding context semantically.

<Card title="Try the API Playground" icon="play" href="/api-reference/endpoint/apply" horizontal>
  Test the Apply Model instantly with live examples
</Card>

<div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
  <div>
    ## Why Choose Fast Apply?

    * **Ultra-fast**: 4,500+ tokens/sec
    * **High accuracy**: 98% success rate in one pass
    * **Token efficient**: Processes only changed sections
  </div>

  <div>
    ### Models

    | Model              | Speed         | Accuracy | Best For            |
    | ------------------ | ------------- | -------- | ------------------- |
    | **morph-v3-fast**  | 4500+ tok/sec | 96%      | Real-time edits     |
    | **morph-v3-large** | 2500+ tok/sec | 98%      | Production systems  |
    | **auto**           | Variable      | \~98%    | Automatic selection |
  </div>
</div>

## Quick Start

<Steps>
  <Step title="Setup Client">
    ```python Python
    from openai import OpenAI

    client = OpenAI(
        api_key="your-morph-api-key",
        base_url="https://api.morphllm.com/v1"
    )
    ```
  </Step>

  <Step title="Apply Changes">
    ```python Python
    def apply_edit(instruction: str, original: str, update: str):
        response = client.chat.completions.create(
            model="morph-v3-large",
            messages=[{
                "role": "user",
                "content": f"<instruction>{instruction}</instruction>\n<code>{original}</code>\n<update>{update}</update>"
            }]
        )
        return response.choices[0].message.content

    # Example
    original = """
    const a = 1
    const authenticateUser = () => {
      return "Authenticated"
    }
    """
    # These should be coming from your Agent
    instruction = "I will change the return text to be French"
    update = """
    // ... existing code ...
      return "Authentifié"
    }
    """

    final_code = apply_edit(instruction, original, update)
    ```
  </Step>
</Steps>

## Best Practices

**Update Snippets**: Use `// ... existing code ...` for unchanged sections:

```javascript
// Good
const authenticateUser = async (email, password) => {
  // ... existing code ...
  const result = await verifyUser(email, password)
  return result ? "Authenticated" : "Unauthenticated"
}
```

**Instructions**: Have the agent write clear, first-person descriptions to "disambiguate uncertainty in the edit":

* ✅ "I will add async/await error handling"
* ❌ "Change this function"

## Next Steps

<CardGroup cols={2}>
  <Card title="API Reference" icon="book" href="/guides/apply">
    Complete technical reference and error handling
  </Card>

  <Card title="Build AI Tools" icon="wrench" href="/guides/tools">
    Integration guide for AI agents
  </Card>
</CardGroup>


anthropic LLM docs:
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    temperature=1,
    system="You are a world-class poet. Respond only with short poems.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Why is the ocean salty?"
                }
            ]
        }
    ]
)
print(message.content)