package com.unitforge.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Inbound DTO for test agent result submissions.
 * Accepted by POST /api/jobs/{id}/results.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AgentResultRequest {

    @NotBlank(message = "moduleName must not be blank")
    private String moduleName;

    private boolean passed;

    @PositiveOrZero(message = "coveragePercent must be >= 0")
    private double coveragePercent;

    private String generatedTestCode;

    private String agentLog;
}
