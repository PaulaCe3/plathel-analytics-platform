import {test} from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ts from "typescript";

const source=fs.readFileSync(new URL("../src/lib/dashboard-exploration.ts",import.meta.url),"utf8");
const output=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
const {toggleDimensionFilter,comparisonSelection}=await import("data:text/javascript;base64,"+Buffer.from(output).toString("base64"));

test("cross-filter toggles, replaces same dimension and accumulates different dimensions",()=>{
 let filters=[];
 filters=toggleDimensionFilter(filters,"category","A");assert.deepEqual(filters,[{field:"category",op:"in",values:["A"]}]);
 filters=toggleDimensionFilter(filters,"category","B");assert.deepEqual(filters,[{field:"category",op:"in",values:["B"]}]);
 filters=toggleDimensionFilter(filters,"channel","Online");assert.equal(filters.length,2);
 filters=toggleDimensionFilter(filters,"category","B");assert.deepEqual(filters,[{field:"channel",op:"in",values:["Online"]}]);
});

test("comparison selection requires one dimension and two distinct values",()=>{
 assert.deepEqual(comparisonSelection("channel","Online","Local"),{dimension:"channel",value_a:"Online",value_b:"Local"});
 assert.equal(comparisonSelection("channel","Online","Online"),undefined);
 assert.equal(comparisonSelection("","Online","Local"),undefined);
});
