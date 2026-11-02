import ts from 'typescript';

// Oxlint checks ordinary component names, but misses anonymous React wrappers.
// Use the existing type-checking program to identify real React APIs and symbols.
export function getComponentNameDiagnostics(program) {
  const checker = program.getTypeChecker();
  const files = program
    .getSourceFiles()
    .filter(
      (file) =>
        !file.isDeclarationFile &&
        !program.isSourceFileFromExternalLibrary(file)
    );
  const namedComponents = new Set();
  const diagnostics = [];

  function symbolAt(node) {
    const symbol = checker.getSymbolAtLocation(node);
    return symbol?.flags & ts.SymbolFlags.Alias
      ? checker.getAliasedSymbol(symbol)
      : symbol;
  }

  function visit(node, inspect) {
    inspect(node);
    ts.forEachChild(node, (child) => visit(child, inspect));
  }

  function ownerOf(call) {
    let current = call;
    while (current.parent) {
      const parent = current.parent;
      if (ts.isVariableDeclaration(parent) && parent.initializer === current) {
        return symbolAt(parent.name);
      }
      if (
        !ts.isCallExpression(parent) &&
        !ts.isParenthesizedExpression(parent)
      ) {
        return undefined;
      }
      current = parent;
    }
    return undefined;
  }

  for (const file of files) {
    visit(file, (node) => {
      if (
        !ts.isBinaryExpression(node) ||
        node.operatorToken.kind !== ts.SyntaxKind.EqualsToken
      )
        return;
      const target = node.left;
      const property = ts.isPropertyAccessExpression(target)
        ? target.name.text
        : ts.isElementAccessExpression(target) &&
            ts.isStringLiteral(target.argumentExpression)
          ? target.argumentExpression.text
          : undefined;
      if (property === 'displayName') {
        const symbol = symbolAt(target.expression);
        if (symbol) namedComponents.add(symbol);
      }
    });
  }

  for (const file of files) {
    visit(file, (node) => {
      if (!ts.isCallExpression(node)) return;
      const declaration = checker.getResolvedSignature(node)?.declaration;
      const name = declaration?.name?.getText();
      const source = declaration
        ?.getSourceFile()
        .fileName.replaceAll('\\', '/');
      if (
        !['memo', 'forwardRef'].includes(name) ||
        !/\/node_modules\/@types\/react\/(?:[^/]+\/)*index\.d\.ts$/.test(
          source ?? ''
        )
      )
        return;
      let render = node.arguments[0];
      while (render && ts.isParenthesizedExpression(render))
        render = render.expression;
      if (
        !render ||
        (!ts.isArrowFunction(render) && !ts.isFunctionExpression(render))
      )
        return;
      if (ts.isFunctionExpression(render) && render.name) return;
      if (namedComponents.has(ownerOf(node))) return;
      diagnostics.push({
        file,
        start: render.getStart(file),
        length: render.getWidth(file),
        category: ts.DiagnosticCategory.Error,
        code: 95001,
        messageText: `Give the function passed to React.${name} a name, or assign a displayName to the returned component.`,
      });
    });
  }
  return diagnostics;
}
