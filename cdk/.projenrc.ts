import { awscdk } from 'projen';
import { NodePackageManager } from 'projen/lib/javascript';
const project = new awscdk.AwsCdkTypeScriptApp({
  cdkVersion: '2.148.1',
  defaultReleaseBranch: 'main',
  name: 'cdk',
  projenrcTs: true,
  context: {
    region: 'us-west-2',
  },
  buildWorkflow: false,
  release: false,
  pullRequestTemplate: false,
  depsUpgrade: false,
  deps: [
    'cdk-nag',
    'fs',
  ],
  githubOptions: {
    pullRequestLint: false,
  },
  packageManager: NodePackageManager.YARN_CLASSIC,
  licensed: false,
  gitignore: ['cdk.context.json'],

  // deps: [],                /* Runtime dependencies of this module. */
  // description: undefined,  /* The description is just a string that helps people understand the purpose of the package. */
  // devDeps: [],             /* Build dependencies for this module. */
  // packageName: undefined,  /* The "name" in package.json. */
});

// package.json に resolutions フィールドを追加
project.addFields({
  resolutions: {
    micromatch: '4.0.8',
  },
});
project.synth();