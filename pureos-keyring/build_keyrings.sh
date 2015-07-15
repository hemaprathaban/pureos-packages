#! /bin/sh

args="--quiet --no-default-keyring"

rm -rf keyrings
mkdir keyrings

echo "building main keyring"
gpg $args --keyring keyrings/pureos-archive-keyring.gpg --import keys/*.asc
gpg $args --keyring keyrings/pureos-archive-keyring.gpg --list-sigs

echo "building automatic keyring"
gpg $args --keyring keyrings/pureos-archive-keyring-automatic.gpg --import keys/automatic.asc
gpg $args --keyring keyrings/pureos-archive-keyring-automatic.gpg --list-sigs

echo "building stable keyring"
gpg $args --keyring keyrings/pureos-archive-keyring-stable.gpg --import keys/stable.asc
gpg $args --keyring keyrings/pureos-archive-keyring-stable.gpg --list-sigs

touch keyrings/pureos-archive-removed-keys.gpg
rm keyrings/*~
