#!usr/bin/env bash

set -e

current_branch=$(git rev-parse --abbrev-ref HEAD)

version=$(poetry version --short)
service=$(poetry version | cut -d ' ' -f1)
service_version="$service-$version"

message="Release Service: $service_version"
echo $message

if [ "$current_branch" != "master" ]
  then
    echo "Releases should be created on master, buddy!"
    echo "Please checkout main on latest and re-run the script."
    echo "Current branch: $current_branch"
    exit -1 
fi

git tag -a $service_version -m "$message"
git push origin $service_version
