# GPG
This page contains instructions for exporting and importing GPG keys.

## Exporting Keys
To export your public and private GPG keys use the following commands.

```
gpg -a --export henrik.treadup@gmail.com > henrik-public-gpg.key
gpg -a --export-secret-keys henrik.treadup@gmail.com > henrik-secret-gpg.key
gpg --export-ownertrust > henrik-ownertrust-gpg.txt
```

## Importing Keys
To import your public and private GPG keys use the following commands.

```
gpg --import henrik-secret-gpg.key
gpg --import-ownertrust henrik-ownertrust-gpg.txt
```

## Trusting Keys
If you forget to import the owner trust you must manually tell GPG that
you trust a key.

    gpg --edit-key henrik.treadup@gmail.com

Then at the GPG prompt you issue the trust command.

    > trust

The trust level for the key should be ultimate trust.
