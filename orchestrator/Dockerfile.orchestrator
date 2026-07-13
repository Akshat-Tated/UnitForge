# ============================================================
# UnitForge — Orchestrator (Spring Boot)
# Multi-stage build:
#   Stage 1 (builder) — Maven compiles the JAR
#   Stage 2 (runtime) — slim JRE runs the JAR
# Final image is ~200MB instead of ~600MB
# ============================================================

# ---- Stage 1: Build ----------------------------------------
FROM maven:3.9-eclipse-temurin-21 AS builder

WORKDIR /app

# Copy pom.xml first and download dependencies
# This layer is cached — only re-runs if pom.xml changes
COPY pom.xml .
RUN mvn dependency:go-offline -q

# Copy source and build
COPY src ./src
RUN mvn package -DskipTests -q

# ---- Stage 2: Runtime --------------------------------------
FROM eclipse-temurin:21-jre-jammy

WORKDIR /app

# Copy only the compiled JAR from builder stage
COPY --from=builder /app/target/*.jar app.jar

# Fix: set timezone to UTC to avoid Asia/Calcutta error with PostgreSQL
ENV JAVA_OPTS="-Duser.timezone=UTC"

EXPOSE 8080

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
