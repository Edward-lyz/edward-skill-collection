# 单文件 diffmap

目标：一个 `<MODEL>_SHADOW_DIFFMAP.html`，双开可用，不联网、不起服务。

## 1. 取 diffmap 前端

```bash
git clone --depth 1 https://github.com/tanishqkancharla/diffmap.git /tmp/diffmap-build
cd /tmp/diffmap-build
npm install --silent --no-audit --no-fund
```

它自带 gist 构建配置；复制一份改为单 chunk：

```ts
// vite.single.config.ts
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const packageRoot = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  root: path.join(packageRoot, "gist"),
  cacheDir: path.join(packageRoot, "node_modules/.vite-single"),
  publicDir: false,
  plugins: [react()],
  appType: "spa",
  resolve: {
    alias: {
      "md4x/napi": path.join(packageRoot, "node_modules/md4x/lib/standalone.mjs"),
    },
    dedupe: ["react", "react-dom", "purse-styles"],
  },
  build: {
    outDir: path.join(packageRoot, "dist-single"),
    emptyOutDir: true,
    assetsInlineLimit: 100_000_000,
    cssCodeSplit: false,
    rolldownOptions: { output: { codeSplitting: false } },
  },
  clearScreen: false,
});
```

```bash
npx vite build --config vite.single.config.ts
```

产物应只有：

```
dist-single/index.html
dist-single/assets/index-*.js     约 14 MB
dist-single/assets/style-*.css   约 300 KB
```

## 2. 内联资源

把 CSS 链接替换为 `<style>...</style>`，把入口 `<script type="module" src>`
替换为内联 `<script type="module">...</script>`。

## 3. 固定路由

diffmap 按 URL 路径解析 gist id；`file://` 下没有 `/g/<id>/`。替换读路由函数：

```js
function HJ(){let e=tSe(window.location.pathname,window.location.hash);if(e!==void 0)return qA(e);let t=qA(window.location.pathname);return t.kind===`empty`?{kind:`home`}:t}
```

改成：

```js
function HJ(){return qA("/g/<GID>/")}
```

`<GID>` 是 32 位十六进制占位 id；离线页面不需要真实 gist。

## 4. 内嵌数据

快照 JSON 结构：

```json
{
  "<full-sha>": {
    "rev": "<full-sha>",
    "title": "[类别] 摘要",
    "files": [
      {
        "path": "python/sglang/...",
        "status": "modified|added|deleted|renamed",
        "additions": 12,
        "deletions": 3,
        "binary": false,
        "contents": { "old": "...", "new": "..." },
        "prevPath": "..."
      }
    ]
  }
}
```

只对文本文件内嵌 `contents`；单文件超过阈值（例如 200 KB）或二进制跳过
内容，保留统计。

把 JSON 用 gzip 压缩后 base64 嵌入 `<script>`，运行时解压：

```js
const bin = Uint8Array.from(atob(B64), c => c.charCodeAt(0));
const stream = new Blob([bin]).stream().pipeThrough(new DecompressionStream("gzip"));
const changes = JSON.parse(await new Response(stream).text());
```

## 5. 接管 Gist 请求

在应用脚本之前覆盖 `window.fetch`：命中
`api.github.com/gists/<GID>` 时返回本地构造的响应：

```json
{
  "id": "<GID>",
  "files": {
    "shadow.md": { "filename": "shadow.md", "content": "<markdown>", "truncated": false },
    "diffmap-changes.json": { "filename": "diffmap-changes.json", "content": "<json string>", "truncated": false }
  }
}
```

其余 GitHub 请求返回 404，非 GitHub 请求透传给原生 fetch。

## 6. 页面内容

Markdown 里每个阶段用：

````
### 阶段 01：[监控] 统一日志与指标

**现状**

...

**调整后**

...

```changes
<full-sha>
python/sglang/srt/...
python/sglang/srt/...
```
````

`changes` 代码块里的 SHA 必须与页面数据、以及推送后分支上的提交一致。

## 7. 验证

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --no-sandbox --disable-gpu \
  --virtual-time-budget=30000 --dump-dom \
  "file:///tmp/<MODEL>_SHADOW_DIFFMAP.html" > /tmp/dom.html
```

确认 DOM 里出现阶段标题和 `N files changed`。若只看到首页，检查路由补丁是否
命中、GID 是否一致、`DecompressionStream` 是否可用。

最后把 HTML 作为 `[文档] 添加 ... 离线 diffmap` 提交放进影子分支根目录。
