package com.unitforge.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CreateJobRequest {

    @NotBlank(message = "inputType must not be blank")
    private String inputType;

    @NotBlank(message = "inputPath must not be blank")
    private String inputPath;
}
