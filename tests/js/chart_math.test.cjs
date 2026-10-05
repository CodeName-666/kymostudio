// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const code = fs.readFileSync('qml/content/ChartTypes/ChartMath.js','utf8').replace(/^\.pragma.*$/gm, '');
const m = {}; vm.createContext(m); vm.runInContext(code,m);
let checks=0;
for (const value of [0, 1, -1, 1e-15, 1e12, 1e308, -1e308]) {
 const r=m.paddedRange(value,value); assert.ok(Number.isFinite(r[0]) && Number.isFinite(r[1]));
 assert.ok(r[0] < r[1]); assert.ok(r[0] <= value && r[1] >= value); checks++;
}
assert.deepEqual(Array.from(m.paddedRange(Infinity,-Infinity)), [0,1]); checks++;
const series={points:[],get count(){return this.points.length;},append(x,y){this.points.push([x,y]);},removePoints(i,n){this.points.splice(i,n);}};
m.appendBatch(series,Array.from({length:20000},(_,i)=>[i,i]),1000,null);
assert.equal(series.count,1000);assert.equal(series.points[0][0],19000);checks++;
m.appendBatch(series,[[20000,1],[NaN,2],[20001,Infinity],[20002,3]],1000,null);
assert.equal(series.count,1000);assert.equal(series.points.at(-1)[0],20002);checks++;
assert.deepEqual(Array.from(m.tail([1,2,3],[4,5,6,7],3)),[5,6,7]);checks++;
assert.deepEqual(Array.from(m.tail([1,2,3],[4],3)),[2,3,4]);checks++;
assert.deepEqual(Array.from(m.zoomRange(0,100,0.5,0.25)),[12.5,62.5]);checks++;
assert.deepEqual(Array.from(m.zoomRange(0,100,2,0.75)),[-75,125]);checks++;
console.log(`${checks} chart-math checks passed`);
