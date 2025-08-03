/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
#include <stddef.h>       // for size_t
#include <stdint.h>
#include "lcd.h"
#include "buzzer.h"
#include "ui.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define VREFINT_CAL (*(uint16_t*)0x1FFF75AA)  // Factory-calibrated ADC value for VREFINT at 3.0 V
#define VREFINT_MV 3000  // Calibration is done at 3.00 V


/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;

RTC_HandleTypeDef hrtc;

SPI_HandleTypeDef hspi1;

TIM_HandleTypeDef htim1;

UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */
#define DRIP_FACTOR_GTT_PER_ML   20      // 20 gtt ≈ 1 mL -- change for your set
#define FLOW_AVG_WINDOW          30      // keep last 30 drops for moving-avg

volatile uint32_t drop_count           = 0;          // running tally
volatile uint32_t last_drop_ms         = 0;          // HAL_GetTick timestamp
volatile uint32_t dt_ms                = 0;          // time between last 2 drops
volatile float    inst_flow_mlh        = 0.0f;       // mL/h from single dt
volatile float    flow_window[FLOW_AVG_WINDOW] = {0};
volatile uint8_t  flow_idx             = 0;          // circular buffer index
volatile float    flow_avg_mlh         = 0.0f;       // moving average flow
volatile float    total_volume_ml      = 0.0f;       // drops ÷ drip-factor
volatile uint16_t target_rate_mlh = 100; // Default: 100 mL/h
volatile uint16_t flow_mlh = 0;



/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_ADC1_Init(void);
static void MX_RTC_Init(void);
static void MX_TIM1_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_SPI1_Init(void);
/* USER CODE BEGIN PFP */
uint32_t  Read_Battery_mV(void);
uint32_t Read_VDDA_mV(void);
uint8_t Battery_mV_to_percent(uint32_t mv);
void LCD_ShowBatteryPercentage(uint8_t percent);

void Monitor_ADC_Drop_Spikes();
void HandleSimulatedDrop(void);

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */


static float MovingAvg_Add(float new_val)
{
    flow_window[flow_idx] = new_val;
    flow_idx = (flow_idx + 1) % FLOW_AVG_WINDOW;

    /* Re-compute running mean (cheap for only 30 samples) */
    float sum = 0.0f;
    for (uint8_t i = 0; i < FLOW_AVG_WINDOW; ++i) sum += flow_window[i];
    return sum / FLOW_AVG_WINDOW;
}


/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_ADC1_Init();
  MX_RTC_Init();
  MX_TIM1_Init();
  MX_USART2_UART_Init();
  MX_SPI1_Init();
  /* USER CODE BEGIN 2 */
  // After MX_TIM1_Init()
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET); //Boost Mode ON
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_3, GPIO_PIN_SET);  // drive gate high → IR LED on

   //Startup Sweep
   for (int freq = 3000; freq <= 4000; freq += 500) {
       Buzzer_PlayFreq(freq, 30);
       HAL_Delay(20);
   }

   printf("BEGIN LCD INITIALIZATION");
   LCD_Init();
   printf("FINISHED LCD INITIALIZATION");

   LCD_Clear();
   LCD_SplashScreen();
   HAL_Delay(1500);
   LCD_Clear();


/*
   for (uint16_t cmd = 0x00; cmd <= 0xFF; cmd++)
   	  {
   		  printf("Sending command: 0x%02X\r\n", cmd);
   		  LCD_WriteCmd((uint8_t)cmd);
   		  HAL_Delay(1);
   	  }*/

   	uint8_t lastBtnMinus = GPIO_PIN_SET;  // button unpressed initially
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {

	  // Track the current line: 0 to 3
	  HandleSimulatedDrop();
	  ui_task();

	  uint32_t batt_mv = Read_Battery_mV();
	  uint8_t  batt_pct = Battery_mV_to_percent(batt_mv);
	  LCD_ShowBatteryPercentage(batt_pct);

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI|RCC_OSCILLATORTYPE_LSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSIDiv = RCC_HSI_DIV1;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.LSIState = RCC_LSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = RCC_PLLM_DIV1;
  RCC_OscInitStruct.PLL.PLLN = 8;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC1_Init(void)
{

  /* USER CODE BEGIN ADC1_Init 0 */

  /* USER CODE END ADC1_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */

  /** Configure the global features of the ADC (Clock, Resolution, Data Alignment and number of conversion)
  */
  hadc1.Instance = ADC1;
  hadc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV2;
  hadc1.Init.Resolution = ADC_RESOLUTION_12B;
  hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
  hadc1.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
  hadc1.Init.LowPowerAutoWait = DISABLE;
  hadc1.Init.LowPowerAutoPowerOff = DISABLE;
  hadc1.Init.ContinuousConvMode = DISABLE;
  hadc1.Init.NbrOfConversion = 1;
  hadc1.Init.DiscontinuousConvMode = DISABLE;
  hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
  hadc1.Init.DMAContinuousRequests = DISABLE;
  hadc1.Init.Overrun = ADC_OVR_DATA_PRESERVED;
  hadc1.Init.SamplingTimeCommon1 = ADC_SAMPLETIME_1CYCLE_5;
  hadc1.Init.SamplingTimeCommon2 = ADC_SAMPLETIME_1CYCLE_5;
  hadc1.Init.OversamplingMode = DISABLE;
  hadc1.Init.TriggerFrequencyMode = ADC_TRIGGER_FREQ_HIGH;
  if (HAL_ADC_Init(&hadc1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Regular Channel
  */
  sConfig.Channel = ADC_CHANNEL_4;
  sConfig.Rank = ADC_REGULAR_RANK_1;
  sConfig.SamplingTime = ADC_SAMPLINGTIME_COMMON_1;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief RTC Initialization Function
  * @param None
  * @retval None
  */
static void MX_RTC_Init(void)
{

  /* USER CODE BEGIN RTC_Init 0 */

  /* USER CODE END RTC_Init 0 */

  /* USER CODE BEGIN RTC_Init 1 */

  /* USER CODE END RTC_Init 1 */

  /** Initialize RTC Only
  */
  hrtc.Instance = RTC;
  hrtc.Init.HourFormat = RTC_HOURFORMAT_24;
  hrtc.Init.AsynchPrediv = 127;
  hrtc.Init.SynchPrediv = 255;
  hrtc.Init.OutPut = RTC_OUTPUT_DISABLE;
  hrtc.Init.OutPutRemap = RTC_OUTPUT_REMAP_NONE;
  hrtc.Init.OutPutPolarity = RTC_OUTPUT_POLARITY_HIGH;
  hrtc.Init.OutPutType = RTC_OUTPUT_TYPE_OPENDRAIN;
  hrtc.Init.OutPutPullUp = RTC_OUTPUT_PULLUP_NONE;
  if (HAL_RTC_Init(&hrtc) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN RTC_Init 2 */

  /* USER CODE END RTC_Init 2 */

}

/**
  * @brief SPI1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_SPI1_Init(void)
{

  /* USER CODE BEGIN SPI1_Init 0 */

  /* USER CODE END SPI1_Init 0 */

  /* USER CODE BEGIN SPI1_Init 1 */

  /* USER CODE END SPI1_Init 1 */
  /* SPI1 parameter configuration*/
  hspi1.Instance = SPI1;
  hspi1.Init.Mode = SPI_MODE_MASTER;
  hspi1.Init.Direction = SPI_DIRECTION_2LINES;
  hspi1.Init.DataSize = SPI_DATASIZE_8BIT;
  hspi1.Init.CLKPolarity = SPI_POLARITY_HIGH;
  hspi1.Init.CLKPhase = SPI_PHASE_2EDGE;
  hspi1.Init.NSS = SPI_NSS_SOFT;
  hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_128;
  hspi1.Init.FirstBit = SPI_FIRSTBIT_MSB;
  hspi1.Init.TIMode = SPI_TIMODE_DISABLE;
  hspi1.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
  hspi1.Init.CRCPolynomial = 7;
  hspi1.Init.CRCLength = SPI_CRC_LENGTH_DATASIZE;
  hspi1.Init.NSSPMode = SPI_NSS_PULSE_DISABLE;
  if (HAL_SPI_Init(&hspi1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN SPI1_Init 2 */

  /* USER CODE END SPI1_Init 2 */

}

/**
  * @brief TIM1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM1_Init(void)
{

  /* USER CODE BEGIN TIM1_Init 0 */

  /* USER CODE END TIM1_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

  /* USER CODE BEGIN TIM1_Init 1 */

  /* USER CODE END TIM1_Init 1 */
  htim1.Instance = TIM1;
  htim1.Init.Prescaler = 63;
  htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim1.Init.Period = 31;
  htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim1.Init.RepetitionCounter = 0;
  htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  if (HAL_TIM_PWM_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterOutputTrigger2 = TIM_TRGO2_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
  sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
  sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
  sBreakDeadTimeConfig.DeadTime = 0;
  sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
  sBreakDeadTimeConfig.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
  sBreakDeadTimeConfig.BreakFilter = 0;
  sBreakDeadTimeConfig.BreakAFMode = TIM_BREAK_AFMODE_INPUT;
  sBreakDeadTimeConfig.Break2State = TIM_BREAK2_DISABLE;
  sBreakDeadTimeConfig.Break2Polarity = TIM_BREAK2POLARITY_HIGH;
  sBreakDeadTimeConfig.Break2Filter = 0;
  sBreakDeadTimeConfig.Break2AFMode = TIM_BREAK_AFMODE_INPUT;
  sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim1, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM1_Init 2 */

  /* USER CODE END TIM1_Init 2 */
  HAL_TIM_MspPostInit(&htim1);

}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart2.Init.ClockPrescaler = UART_PRESCALER_DIV1;
  huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_RXOVERRUNDISABLE_INIT|UART_ADVFEATURE_DMADISABLEONERROR_INIT;
  huart2.AdvancedInit.OverrunDisable = UART_ADVFEATURE_OVERRUN_DISABLE;
  huart2.AdvancedInit.DMADisableonRxError = UART_ADVFEATURE_DMA_DISABLEONRXERROR;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */
  /* --- DOGS164 control lines: PB0 = /CS, PB1 = /RST, PB14 = A0 --- */
  GPIO_InitStruct.Pin   = LCD_CS_Pin | LCD_RESET_Pin | GPIO_PIN_14;
  GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull  = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* Initial idle levels */
  HAL_GPIO_WritePin(LCD_CS_GPIO_Port,  LCD_CS_Pin,  GPIO_PIN_SET);   // /CS high (inactive)
  HAL_GPIO_WritePin(LCD_RESET_GPIO_Port, LCD_RESET_Pin, GPIO_PIN_SET);   // RST high (normal operation)
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_RESET);     // A0 low (command)

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, LCD_CS_Pin|LCD_RESET_Pin|BOOST_MODE_CTRL_Pin, GPIO_PIN_SET);

  /*Configure GPIO pins : LCD_CS_Pin LCD_RESET_Pin */
  GPIO_InitStruct.Pin = LCD_CS_Pin|LCD_RESET_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pin : DROP_INT_Pin */
  GPIO_InitStruct.Pin = DROP_INT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(DROP_INT_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : BOOST_MODE_CTRL_Pin */
  GPIO_InitStruct.Pin = BOOST_MODE_CTRL_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_MEDIUM;
  HAL_GPIO_Init(BOOST_MODE_CTRL_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : BTN_MINUS_Pin BTN_PLUS_Pin BTN_MODE_Pin BTN_MUTE_Pin */
  GPIO_InitStruct.Pin = BTN_MINUS_Pin|BTN_PLUS_Pin|BTN_MODE_Pin|BTN_MUTE_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */
  GPIO_InitStruct.Pin = GPIO_PIN_6;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_6, GPIO_PIN_SET); // Default to DATA mode


  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
uint8_t Battery_mV_to_percent(uint32_t mv)
{
    if (mv <= 700)  return 0;
    if (mv >= 1500) return 100;

    if (mv < 1100) {
        return (uint8_t)((mv - 700) * 25 / 400);
    } else if (mv < 1250) {
        return 25 + (uint8_t)((mv - 1100) * 35 / 150);
    } else if (mv < 1350) {
        return 60 + (uint8_t)((mv - 1250) * 25 / 100);
    } else {
        return 85 + (uint8_t)((mv - 1350) * 15 / 150);
    }
}


/* USER CODE END BatteryPct */

void Monitor_ADC_Drop_Spikes(void)
{
    const float spike_threshold_mV = 1700.0f;   // Voltage threshold for spike detection
    static float previous_voltage_mv = 0.0f;    // Store previous measurement
    const uint32_t sampling_interval_ms = 1;   // 100 Hz sampling rate (adjust as needed)

    // Read VDDA voltage once per iteration
    uint32_t vdda_mv = Read_VDDA_mV();

    // Configure ADC Channel for PD_ADC (PA3)
    ADC_ChannelConfTypeDef adcConfig = {0};
    adcConfig.Channel = ADC_CHANNEL_3;
    adcConfig.Rank = ADC_REGULAR_RANK_1;
    adcConfig.SamplingTime = ADC_SAMPLINGTIME_COMMON_1;
    HAL_ADC_ConfigChannel(&hadc1, &adcConfig);

    // Start ADC Conversion
    HAL_ADC_Start(&hadc1);
    HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);
    uint32_t adc_raw = HAL_ADC_GetValue(&hadc1);
    HAL_ADC_Stop(&hadc1);

    // Calculate voltage in mV
    float voltage_mv = ((float)adc_raw * vdda_mv) / 4095.0f;

    // Print debug information
    //printf("ADC raw: %lu, Voltage: %.2f mV, VDDA: %lu mV, Previous: %.2f mV\r\n",
    //       adc_raw, voltage_mv, vdda_mv, previous_voltage_mv);

    // Spike Detection Logic
    if ((voltage_mv > spike_threshold_mV) && (previous_voltage_mv <= spike_threshold_mV))
    {
        /* ----------  DROP DETECTED  ---------- */
        uint32_t now = HAL_GetTick();            // ms since boot

        /* First drop has no dt */
        if (drop_count > 0)
        {
            dt_ms = now - last_drop_ms;
            /* convert dt to instantaneous flow: 3600 s/h × 1000 ms/s */
            inst_flow_mlh = (3600.0f * 1000.0f) / ((float)dt_ms * DRIP_FACTOR_GTT_PER_ML);
            flow_avg_mlh  = MovingAvg_Add(inst_flow_mlh);
        }
        last_drop_ms = now;
        drop_count++;

        total_volume_ml = (float)drop_count / DRIP_FACTOR_GTT_PER_ML;

        /* Battery */
        uint32_t batt_mv  = Read_Battery_mV();
        uint8_t  batt_pct = Battery_mV_to_percent(batt_mv);

        /* Time since power-up */
        uint32_t elapsed_ms = now;                       // HAL_GetTick base = boot
        uint32_t elapsed_s  = elapsed_ms / 1000;

        /* -------------------------------------------------------------- */
        /*  DROP DETECTED  — single-line logger                           */
        /* -------------------------------------------------------------- */
        printf("DROP %lu | Δt: %lums | Rate: %.0f mL/h | Total: %.2f mL | Time: %lu:%02lu min\r\n",
               drop_count,
               dt_ms,
               inst_flow_mlh,
               total_volume_ml,
               elapsed_s / 60,
               elapsed_s % 60);
    }

    char flow_str[17];  // 16 chars + null terminator
    snprintf(flow_str, sizeof(flow_str), "Rate: %4.0f mL/h", inst_flow_mlh);
    //LCD_Print(1, flow_str);  // Show on line 1 (second line)


    // Store current measurement as previous for next iteration
    previous_voltage_mv = voltage_mv;

    // Delay before next sampling
    HAL_Delay(sampling_interval_ms);
}


uint32_t Read_VDDA_mV(void)
{
    ADC_ChannelConfTypeDef sConfig = {0};
    sConfig.Channel = ADC_CHANNEL_VREFINT;
    sConfig.Rank = ADC_REGULAR_RANK_1;
    sConfig.SamplingTime = ADC_SAMPLETIME_19CYCLES_5;
    HAL_ADC_ConfigChannel(&hadc1, &sConfig);

    HAL_ADC_Start(&hadc1);
    HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);
    uint32_t vrefint_adc = HAL_ADC_GetValue(&hadc1);
    HAL_ADC_Stop(&hadc1);

    // VDDA (real) = 3.000 V × (VREFINT_CAL / measured VREFINT)
    return (VREFINT_CAL * VREFINT_MV) / vrefint_adc;  // in millivolts
}
uint32_t Read_Battery_mV(void)
{
    uint32_t vdda_mv = Read_VDDA_mV();

    ADC_ChannelConfTypeDef sConfig = {0};
    sConfig.Channel = ADC_CHANNEL_4;  // PA4
    sConfig.Rank = ADC_REGULAR_RANK_1;
    sConfig.SamplingTime = ADC_SAMPLETIME_19CYCLES_5;
    HAL_ADC_ConfigChannel(&hadc1, &sConfig);

    HAL_ADC_Start(&hadc1);
    HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);
    uint32_t adc_val = HAL_ADC_GetValue(&hadc1);
    HAL_ADC_Stop(&hadc1);

    return (adc_val * vdda_mv) / 4095;  // Battery voltage at PA4 in mV
}

/* ---------- LCD stats helpers ------------------------------------------ */
void UpdateStatsDisplay(void)
{
    /* Elapsed time since power-up */
    uint32_t elapsed_ms = HAL_GetTick();
    uint32_t hrs  = elapsed_ms / 3600000UL;
    uint32_t mins = (elapsed_ms / 60000UL) % 60;
    uint32_t secs = (elapsed_ms / 1000UL)  % 60;

    char time_str[17];
    snprintf(time_str, sizeof(time_str), "%02lu:%02lu:%02lu", hrs, mins, secs);

    /* Total infused volume */
    char vol_str[17];
    snprintf(vol_str, sizeof(vol_str), "Vol: %4.1f mL", total_volume_ml);
    //LCD_Print(2, vol_str);           // third line
}

/* ---------- PLUS-button drop simulator --------------------------------- */
void HandleSimulatedDrop(void)
{
    static uint8_t lastBtnPlus = GPIO_PIN_SET;      // unpressed
    uint8_t nowPlus = HAL_GPIO_ReadPin(GPIOB, BTN_PLUS_Pin);

    if (nowPlus == GPIO_PIN_RESET && lastBtnPlus == GPIO_PIN_SET)
    {
        /* Simulated drop */
        uint32_t now = HAL_GetTick();

        if (drop_count > 0) {
            dt_ms = now - last_drop_ms;
            inst_flow_mlh = (3600.0f * 1000.0f) /
                            ((float)dt_ms * DRIP_FACTOR_GTT_PER_ML);
            flow_avg_mlh  = MovingAvg_Add(inst_flow_mlh);
        }

        last_drop_ms = now;
        drop_count++;
        total_volume_ml = (float)drop_count / DRIP_FACTOR_GTT_PER_ML;

        char rate_str[17];
        snprintf(rate_str, sizeof(rate_str), "Rate: %4.0f mL/h", inst_flow_mlh);
        //LCD_Print(1, rate_str);       // middle line

        UpdateStatsDisplay();         // update time + volume

        Buzzer_PlayFreq(3000, 30);    // audible feedback
        HAL_Delay(200);               // debounce
    }

    lastBtnPlus = nowPlus;
}


/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
	  //Monitor_ADC_Drop_Spikes();
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
