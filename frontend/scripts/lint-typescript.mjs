import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative } from 'node:path';
import ts from 'typescript';

const root = process.cwd();
const lintRoots = ['src'];
const lintExtensions = new Set(['.ts', '.tsx']);

const forbiddenIdentifiers = new Map([
  ['fit', 'Focused tests must not be committed.'],
  ['fdescribe', 'Focused test suites must not be committed.'],
  ['xit', 'Disabled tests must not be committed.'],
  ['xdescribe', 'Disabled test suites must not be committed.'],
]);

const failures = [];
let checkedFiles = 0;

function collectFiles(dir) {
  const files = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name === 'dist') continue;
    const absolute = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...collectFiles(absolute));
      continue;
    }
    if (lintExtensions.has(extname(entry.name))) files.push(absolute);
  }
  return files;
}

function locationFor(sourceFile, node) {
  const { line, character } = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
  return `${relative(root, sourceFile.fileName)}:${line + 1}:${character + 1}`;
}

function report(sourceFile, node, message) {
  failures.push(`${locationFor(sourceFile, node)} - ${message}`);
}

function isConsoleLog(node) {
  return (
    ts.isCallExpression(node) &&
    ts.isPropertyAccessExpression(node.expression) &&
    node.expression.expression.getText() === 'console' &&
    node.expression.name.text === 'log'
  );
}

function visit(sourceFile, node) {
  if (node.kind === ts.SyntaxKind.DebuggerStatement) {
    report(sourceFile, node, 'Unexpected debugger statement.');
  }

  if (isConsoleLog(node)) {
    report(sourceFile, node, 'Unexpected console.log statement.');
  }

  if (ts.isCallExpression(node) && ts.isIdentifier(node.expression)) {
    const message = forbiddenIdentifiers.get(node.expression.text);
    if (message) report(sourceFile, node.expression, message);
  }

  ts.forEachChild(node, (child) => visit(sourceFile, child));
}

for (const lintRoot of lintRoots) {
  for (const file of collectFiles(join(root, lintRoot))) {
    checkedFiles += 1;
    const text = readFileSync(file, 'utf8');
    const sourceKind = extname(file) === '.tsx' ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
    const sourceFile = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, sourceKind);
    visit(sourceFile, sourceFile);
  }
}

if (checkedFiles === 0) {
  failures.push('No TypeScript or TSX files were checked.');
}

if (failures.length > 0) {
  console.error(`TypeScript lint failed with ${failures.length} issue(s):`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`TypeScript lint checked ${checkedFiles} file(s).`);
