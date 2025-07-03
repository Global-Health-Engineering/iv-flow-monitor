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
#include "stm32g0xx_hal.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define CS_Pin        GPIO_PIN_0
#define CS_GPIO_Port  GPIOB
#define RST_Pin       GPIO_PIN_1
#define RST_GPIO_Port GPIOB
#define BTN_MINUS_Pin GPIO_PIN_6
#define BTN_PLUS_Pin  GPIO_PIN_7
#define BTN_MODE_Pin  GPIO_PIN_8
#define BTN_MUTE_Pin  GPIO_PIN_9
#define BTN_PORT      GPIOB
#define VREFINT_CAL (*(uint16_t*)0x1FFF75AA)  // Factory-calibrated ADC value for VREFINT at 3.0 V
#define VREFINT_MV 3000  // Calibration is done at 3.00 V

#define DROP_VOLUME_ML     0.05f
#define DEAD_DROP_TIMEOUT_MS 10000  // 10 seconds
#define LOCKOUT_MS 100  // Debounce lockout time

#define DOG_TRACE   1

#if DOG_TRACE
  #define TRACE(...)   printf(__VA_ARGS__)
#else
  #define TRACE(...)
#endif


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
void Monitor_Drops_WithFlow();

/* DOGS164 helpers ----------------------------------------------------------*/
void DOG_WriteCommand(uint8_t cmd);
void DOG_WriteData(uint8_t dat);
void DOG_Init(void);

static inline void DOG_Select(void)   { HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET); }
static inline void DOG_Deselect(void) { HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);  }
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/* ------------------------------------------------------------------------- */
/*  EA-DOGS164-A  SPI helpers (SSD1803A, 3-byte frames, mode-3 @ ≤1 MHz)     */
/* ------------------------------------------------------------------------- */
uint8_t DOG_ReadStatus(void)
{
    uint8_t status;

    DOG_Select();

    // Status read command for SSD1803A is typically 0xFC (check your datasheet to confirm)
    uint8_t read_cmd = 0xFC;
    HAL_SPI_Transmit(&hspi1, &read_cmd, 1, HAL_MAX_DELAY);
    HAL_SPI_Receive(&hspi1, &status, 1, HAL_MAX_DELAY);

    DOG_Deselect();

    printf("DOG Status: 0x%02X\r\n", status);
    return status;
}

/* --------------------------------------------------------------------------
 *  DOGS164 low-level serial driver
 * -------------------------------------------------------------------------*/


/* comment this line out if you don’t want the printf-traces */


extern SPI_HandleTypeDef hspi1;               /* created by CubeMX */


/* ---------- generic 3-wire frame (cmd or data) -------------------------- */
static HAL_StatusTypeDef DOG_WriteFrame(uint8_t sync, uint8_t value)
{
    uint8_t frame[3] =
    {
        sync,                 /* 0xF8 = command, 0xFA = data              */
        value       & 0xF0,   /* upper nibble first                        */
       (value << 4) & 0xF0    /* lower nibble second                       */
    };

    TRACE("A0: %s, CS LOW, SPI: %02X %02X %02X\r\n",
          (sync == 0xFA) ? "DATA" : "CMD",
          frame[0], frame[1], frame[2]);

    DOG_Select();
    HAL_StatusTypeDef res = HAL_SPI_Transmit(&hspi1, frame, 3, HAL_MAX_DELAY);
    DOG_Deselect();

    TRACE("CS HIGH, SPI Status: %d\r\n", res);
    return res;
}

/* ---------- wrappers ---------------------------------------------------- */
void DOG_WriteCommand(uint8_t cmd)
{
    TRACE("DOG CMD 0x%02X\r\n", cmd);
    DOG_WriteFrame(0xF8, cmd);
}

void DOG_WriteData(uint8_t dat)
{
    TRACE("DOG DAT 0x%02X\r\n", dat);
    DOG_WriteFrame(0xFA, dat);
}

/* --------------------------------------------------------------------------
 *  Because BF (bit7) cannot be read in serial mode (SSD1803A data-sheet
 *  §9.19, note 1) we simply wait the times given in Fig 13-8.
 * -------------------------------------------------------------------------*/
static inline void DOG_ShortDelay (void) { HAL_Delay(  20); }   /* ≥ 1 ms   */
static inline void DOG_LongDelay  (void) { HAL_Delay(200); }   /* ≥ 200 ms */

void DOG_Init(void)
{
    /* --- hard reset ----------------------------------------------------- */
    HAL_GPIO_WritePin(RST_GPIO_Port, RST_Pin, GPIO_PIN_RESET);
    HAL_Delay(20);
    HAL_GPIO_WritePin(RST_GPIO_Port, RST_Pin, GPIO_PIN_SET);
    HAL_Delay(100);

    /* --- initialisation sequence (4-line, bottom-view) ------------------ */
    DOG_WriteCommand(0x3A);           /* Function set   RE=1              */
    DOG_WriteCommand(0x09);           /* 4-line display                    */
    DOG_WriteCommand(0x1E);           /* Bias 1/5                          */

    DOG_WriteCommand(0x39);           /* Function set   RE=0, IS=1         */
    DOG_WriteCommand(0x1B);           /* Internal OSC freq                 */

    DOG_WriteCommand(0x6C);           /* Follower ON                       */
    DOG_LongDelay();                  /* 200 ms                            */

    DOG_WriteCommand(0x56);           /* Power control                     */
    DOG_ShortDelay();                 /* 20 ms + is plenty                 */

    DOG_WriteCommand(0x72);           /* Contrast                          */

    DOG_WriteCommand(0x38);           /* Function set   RE=0, IS=0         */
    DOG_WriteCommand(0x0F);           /* Display ON, cursor+blink ON       */
}



static void Buzzer_SetDuty(uint16_t duty)
{
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, duty);
}
void Buzzer_PlayFreq(uint16_t freq, uint16_t duration_ms)
{
    uint32_t timer_clk = 1000000;  // TIM1 clock after prescaler = 64 MHz / (63 + 1)
    uint32_t period = timer_clk / freq;

    __HAL_TIM_SET_AUTORELOAD(&htim1, period - 1);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, period / 2);  // 50% duty
    HAL_Delay(duration_ms);
    Buzzer_SetDuty(0);
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
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_3, GPIO_PIN_SET);  // drive gate high → IR LED on

   //Startup Sweep
   for (int freq = 3000; freq <= 4000; freq += 100) {
       Buzzer_PlayFreq(freq, 30);
       HAL_Delay(20);
   }

  printf("Init start\r\n");
  DOG_Init();

  printf("Reading DOGS164 status:\r\n");
  for (int i = 0; i < 5; i++) {
      uint8_t status = DOG_ReadStatus();
      HAL_Delay(500);
  }

  HAL_Delay(5000);
  printf("SPI1 Mode: %lu, Direction: %lu\r\n", hspi1.Init.Mode, hspi1.Init.Direction);

  printf("DOG_Init done\r\n");
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
	  Monitor_Drops_WithFlow();
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
  sConfig.Channel = ADC_CHANNEL_3;
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
  hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_64;
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
  GPIO_InitStruct.Pin   = CS_Pin | RST_Pin | GPIO_PIN_14;
  GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull  = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* Initial idle levels */
  HAL_GPIO_WritePin(CS_GPIO_Port,  CS_Pin,  GPIO_PIN_SET);   // /CS high (inactive)
  HAL_GPIO_WritePin(RST_GPIO_Port, RST_Pin, GPIO_PIN_SET);   // RST high (normal operation)
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_RESET);     // A0 low (command)

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0|LCD_RST_Pin|GPIO_PIN_3, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(BOOST_MODE_CTRL_GPIO_Port, BOOST_MODE_CTRL_Pin, GPIO_PIN_SET);

  /*Configure GPIO pins : PB0 LCD_RST_Pin PB3 */
  GPIO_InitStruct.Pin = GPIO_PIN_0|LCD_RST_Pin|GPIO_PIN_3;
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

  /* EXTI interrupt init*/
  HAL_NVIC_SetPriority(EXTI4_15_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI4_15_IRQn);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

void Monitor_Drops_WithFlow(void)
{
    static uint32_t last_drop_time_ms = 0;
    static uint32_t drop_count = 0;
    static float total_volume_ml = 0.0f;

    uint32_t current_time_ms = HAL_GetTick();
    uint32_t delta_t_ms = current_time_ms - last_drop_time_ms;

    // === Sample ADC ===
    uint32_t vdda_mv = Read_VDDA_mV();

    ADC_ChannelConfTypeDef adcConfig = {0};
    adcConfig.Channel = ADC_CHANNEL_3;
    adcConfig.Rank = ADC_REGULAR_RANK_1;
    adcConfig.SamplingTime = ADC_SAMPLINGTIME_COMMON_1;
    HAL_ADC_ConfigChannel(&hadc1, &adcConfig);

    HAL_ADC_Start(&hadc1);
    HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);
    uint32_t adc_raw = HAL_ADC_GetValue(&hadc1);
    HAL_ADC_Stop(&hadc1);

    float voltage_mv = ((float)adc_raw * vdda_mv) / 4095.0f;

    // === Drop Detected ===
    if ((voltage_mv > 1800.0f) && (delta_t_ms > LOCKOUT_MS))
    {
        drop_count++;
        total_volume_ml += DROP_VOLUME_ML;
        last_drop_time_ms = current_time_ms;

        float delta_t_sec = (float)delta_t_ms / 1000.0f;
        float ml_per_h = (DROP_VOLUME_ML / delta_t_sec) * 3600.0f;
        float drops_per_min = 60.0f / delta_t_sec;

        printf("DROP #%lu at %lu ms | Δt = %lu ms | Rate: %.1f ml/h (%.1f drops/min) | Total: %.2f ml\r\n",
               drop_count, current_time_ms, delta_t_ms, ml_per_h, drops_per_min, total_volume_ml);
    }

    // === Dead-drop detection ===
    static uint8_t alarm_triggered = 0;
    if ((current_time_ms - last_drop_time_ms) > DEAD_DROP_TIMEOUT_MS)
    {
        if (!alarm_triggered)
        {
            printf("ALARM: No drop detected for %lu ms. Flow interruption suspected.\r\n",
                   DEAD_DROP_TIMEOUT_MS);
            for(int i = 0; i < 3; i++){
            	Buzzer_PlayFreq(2000, 500);  // 2 kHz for 500 ms
            	HAL_Delay(100);
            }
            alarm_triggered = 1;
        }
    }
    else
    {
        // Reset alarm flag if flow resumed
        alarm_triggered = 0;
    }

    HAL_Delay(1);  // Sampling delay ~1000 Hz
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
