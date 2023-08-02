package com.connexta.keip.container;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ImportResource;
import org.springframework.integration.config.EnableIntegration;

@SpringBootApplication
@EnableIntegration
@ImportResource(locations = "${integration.file.path:file:/var/spring/xml/integrationRoute.xml}")
public class SpringIntegrationApplication {
    public static void main(String[] args) {
        SpringApplication.run(SpringIntegrationApplication.class);
    }
}
