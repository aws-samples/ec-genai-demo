import * as fs from 'fs';
import { App, Aspects, Stack } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { AwsSolutionsChecks } from 'cdk-nag';
import { EcGenaiDemo } from '../src/main';
import { applySuppressions } from '../src/nagSuppressions';
let outputStream: fs.WriteStream;

describe('cdk-nag AwsSolutions Pack', () => {
  let stack: Stack;
  let app: App;

  beforeEach(() => {
    app = new App();
    stack = new EcGenaiDemo(app, 'CDKNagWithProjen', {});

    outputStream = fs.createWriteStream('cdk-nag-output.txt');
  });

  afterEach(() => {
    outputStream.end();
  });

  test('Output all Warnings and Errors', () => {
    Aspects.of(stack).add(
      new AwsSolutionsChecks({
        verbose: true,
        logIgnores: false,
      }),
    );

    const warnings = Annotations.fromStack(stack).findWarning(
      '*',
      Match.stringLikeRegexp('AwsSolutions-.*'),
    );

    outputStream.write('All Warnings:\n');
    warnings.forEach((warning) => {
      outputStream.write(warning.entry.data);
    });

    const errors = Annotations.fromStack(stack).findError(
      '*',
      Match.stringLikeRegexp('AwsSolutions-.*'),
    );

    outputStream.write('All Errors:\n');
    errors.forEach((error) => {
      outputStream.write(error.entry.data);
    });
  });
  test('No unsuppressed Warnings or Errors after applying suppressions', () => {
    applySuppressions(stack);

    Aspects.of(stack).add(
      new AwsSolutionsChecks({
        verbose: true,
        logIgnores: false,
      }),
    );

    const unsuppressedWarnings = Annotations.fromStack(stack).findWarning(
      '*',
      Match.stringLikeRegexp('AwsSolutions-.*'),
    );

    expect(unsuppressedWarnings).toHaveLength(0);

    const unsuppressedErrors = Annotations.fromStack(stack).findError(
      '*',
      Match.stringLikeRegexp('AwsSolutions-.*'),
    );

    expect(unsuppressedErrors).toHaveLength(0);
  });

});
