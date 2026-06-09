import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const skillDir = resolve(scriptDir, '..');
const payloadPath = process.argv[2];
const outputPath = process.argv[3];

if (!payloadPath || !outputPath) {
  throw new Error('usage: node render_crabviz_html.mjs payload.json output.html');
}

const crabvizModulePath = resolve(skillDir, 'assets/crabviz/index.js');
const { initSync, GraphGenerator, set_panic_hook } = await import(pathToFileURL(crabvizModulePath));
initSync({ module: readFileSync(resolve(skillDir, 'assets/crabviz/index_bg.wasm')) });
set_panic_hook();

const payload = JSON.parse(readFileSync(payloadPath, 'utf8'));
const graphGenerator = new GraphGenerator(payload.language_name, false);

for (const [path, symbols] of Object.entries(payload.files)) {
  graphGenerator.add_file(path, symbols);
}

for (const [sourceKey, outgoingCalls] of Object.entries(payload.outgoing)) {
  const parts = sourceKey.split(':');
  const character = Number(parts.pop());
  const line = Number(parts.pop());
  const path = parts.join(':');
  graphGenerator.add_outgoing_calls(path, { line, character }, outgoingCalls);
}

for (const [targetKey, incomingCalls] of Object.entries(payload.incoming)) {
  const parts = targetKey.split(':');
  const character = Number(parts.pop());
  const line = Number(parts.pop());
  const path = parts.join(':');
  graphGenerator.add_incoming_calls(path, { line, character }, incomingCalls);
}

const graph = graphGenerator.gen_graph();
const css = readFileSync(resolve(skillDir, 'assets/webview-ui/index.css'), 'utf8');
const js = readFileSync(resolve(skillDir, 'assets/webview-ui/index.js'), 'utf8');
const title = `${payload.seed_label} LSP callgraph`;
const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>${title.replaceAll('&', '&amp;').replaceAll('<', '&lt;')}</title>
<style>${css}</style>
<script>
document.crabvizProps = ${JSON.stringify({ graph, root: payload.root, focus: null })};
window.addEventListener('message', (event) => console.log(event.data));
</script>
</head>
<body><div id="root"></div><script type="module">${js}</script></body>
</html>`;

writeFileSync(outputPath, html);
console.log(JSON.stringify({ outputPath, files: graph.files.length, relations: graph.relations.length }, null, 2));
