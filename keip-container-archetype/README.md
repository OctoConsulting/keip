# Keip Container Archetype

Because Spring Integration is able to connect to so many different protocols, the default keip container is necessarily 
basic. This archetype will simplify the process of creating a custom container with the Spring Integration dependencies
needed for your specific project.

## Creating a custom Keip container

The process for creating a custom keip container is outlined here:

1. build this archtetype: `mvn clean install`
2. change to a directory where you want to create a new project: `cd ..`
3. issue the following command (change the values of groupId, artifactId and version to suit your needs):

```shell 
mvn archetype:generate -DinteractiveMode=false \
                       -DarchetypeCatalog=local \
                       -DarchetypeGroupId=com.octo.keip \
                       -DarchetypeArtifactId=keip-container-archetype \
                       -DarchetypeVersion=0.0.1-SNAPSHOT \
                       -DgroupId=com.acme \
                       -DartifactId=rocket-skis \
                       -Dversion=0.1.0-SNAPSHOT
```

4. change to the new directory: `cd rocket-skis`
5. edit the `pom.xml` file to include any dependencies required for your project or remove those that aren't required.
6. build the container: `mvn clean install`

This example will create a new Docker container called `rocket-skis:0.1.0-SNAPSHOT`