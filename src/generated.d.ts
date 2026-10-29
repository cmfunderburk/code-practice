// The bundle is large and typed by hand in bundle.ts, so the type checker
// doesn't infer a type from its contents.
declare module '*/generated/bundle.json' {
  const value: unknown;
  export default value;
}
