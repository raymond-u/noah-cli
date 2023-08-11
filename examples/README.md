# Examples

## Initialize a new project

Use the `noah init` command to create a new project in the current directory:

```bash
noah init
```

Or to create a new project in the `my_project` directory:

```bash
noah init my_project # This will by default create a Git repository in my_project
cd my_project
```

## Add datasets to a project

Use the `noah add` command to add new datasets to your project:

```bash
noah add SRP123456 SRX123456 ENCSR123ABC GSE123456 GSM123456
```

This will automatically retrieve the metadata from public databases, download the files to the `data` directory, and write the `noah.yaml` file.

To add local files:

```bash
noah add /path/to/my_dataset/read_{1,2}.fastq.gz # Paired-end reads will be automatically detected
```

To add privately hosted datasets:

```bash
noah add me@some_host:path/to/my_dataset https://example.com/some_dataset ftp://ftp.example.com/another_dataset
```

Every dataset is associated with its metadata, including a project name, an experiment name, a library type, and a pipeline phase.

To input the metadata manually, you can pass extra options to the command in the form of `value` to match all datasets, or `key:value` to match specific datasets, separated by commas:

```bash
noah add my_project/my_dataset --project my_project --experiment my_experiment --library-type chip --pipeline-phase raw
noah add SRP123456 --library_type SRX123:chip-input,SRX456:chip-input # Override the metadata of public datasets
```

The matching order is as follows:

`key:value` has higher priority than wildcard, and can override the metadata of any dataset that matches the key.

Wildcard only matches those datasets whose metadata cannot be retrieved from public databases, such as local files or datasets hosted on private servers.

If any of the metadata is still missing, you will be prompted to input them manually.

## Remove datasets from a project

Use the `noah remove` command to remove existing datasets from your project:

```bash
noah remove SRP123456 SRX123456
```

Use directory names to remove all datasets in a directory is also allowed:

```bash
noah remove my_project/my_dataset # Remove all datasets that have the my_project/my_dataset prefix
noah remove my_project/my_dataset@chip # Remove all datasets in the my_project/my_dataset@chip directory
```

To remove all datasets:

```bash
noah remove .
```

## Check the status of files in a project

Use the `noah check` command to check if everything is there:

```bash
noah check
```

To also verify the integrity of files:

```bash
noah check --verify
```

## Retrieve files for a project

Use the `noah install` command to retrieve files for a project:

```bash
noah install
```

## Offload files for a project

Use the `noah uninstall` command to offload files for a project, in case you need to free up some disk space:

```bash
noah uninstall
```

## Edit the information about a project

Use the `noah info show` command to print the information about a project:

```bash
noah info show
```

Use the `noah info edit` command to edit the information about a project:

```bash
noah info edit
noah info edit author # Edit the author information
```

## Publish a project

The recommended way to publish a project is to push it to GitHub, for example:

```bash
git add .
git commit -m 'Initial commit'
git remote add origin git@github.com:me/my_project.git
git push -u origin main
```

Files managed by Noah will be ignored by default, including the `containers` directory, the `data` directory, etc. They can be easily restored by running `noah install`.
