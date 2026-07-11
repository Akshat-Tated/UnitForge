package com.unitforge.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TestResultResponse {

    private UUID id;
    private UUID jobId;
    private String moduleName;
    private boolean passed;
    private double coveragePercent;
    private String generatedTestCode;
    private String agentLog;
    private Instant createdAt;
}
