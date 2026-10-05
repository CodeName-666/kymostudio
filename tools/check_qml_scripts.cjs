#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
/** Lightweight JS syntax check, NOT a QML compiler or Qt runtime substitute.
 * No third-party npm dependencies. Parses .js files (without QML pragmas) and
 * function bodies embedded in QML. Bindings/types/layout still require Qt.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const base = path.resolve(__dirname, '..', 'qml');
function walk(dir) {
  return fs.readdirSync(dir, {withFileTypes: true}).flatMap(e =>
    e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]);
}
function mask(source) {
  // Preserve source positions while ignoring comments and quoted literals.
  return source.replace(/\/\*[\s\S]*?\*\/|\/\/[^\r\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`/g,
    value => value.replace(/[^\r\n]/g, ' '));
}
let functions = 0, scripts = 0, files = 0;
for (const filename of walk(base)) {
  if (!/\.(qml|js)$/.test(filename)) continue;
  const source = fs.readFileSync(filename, 'utf8'); files++;
  if (filename.endsWith('.js')) {
    new vm.Script(source.replace(/^\s*\.(import|pragma).*$/gm, ''), {filename}); scripts++;
    continue;
  }
  const code = mask(source);
  const re = /\bfunction\s*(?:[$\w]+\s*)?\(/g;
  for (const match of code.matchAll(re)) {
    let start = code.indexOf('{', match.index), end = start + 1, depth = 1;
    if (start < 0) throw new Error(`Function body missing in ${filename}`);
    for (; end < code.length && depth; end++) {
      if (code[end] === '{') depth++;
      else if (code[end] === '}') depth--;
    }
    if (depth) throw new Error(`Unbalanced function at ${filename}:${match.index}`);
    const snippet = source.slice(match.index, end);
    new vm.Script('(' + snippet + ')', {filename}); functions++;
  }
}
console.log(`${files} QML/JS files examined: ${scripts} standalone scripts and ${functions} embedded JavaScript functions parse successfully.`);
console.log('QML type resolution, declarative bindings, native APIs and rendering are NOT checked here. Run the Qt smoke test.');
