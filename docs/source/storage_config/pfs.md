# PFS

Lithops with Parallel Filesystem storage backend.


## Installation

1. The backend assumes a parallel filesystem is mounted in a local directory.

## Configuration

Edit your Lithops config file and add the following keys:

```yaml
lithops:
    storage: pfs

pfs:
    storage_root: /path/to/dir/in/mounted/pfs
    storage_bucket: <BUCKET_NAME>
```

## Summary of configuration keys for PFS

|Group|Key|Default|Mandatory|Additional info|
|---|---|---|---|---|
|pfs | storage_root | |yes | Path to a directory within the locally mounted PFS that will serve as storage root. |
|pfs | storage_bucket | | no | The name of a bucket that will be emulated as a directory inside the storage root directory. This will be used by Lithops for intermediate data. Lithops will automatically create a new one if it is not provided. |
