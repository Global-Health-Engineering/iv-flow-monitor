/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
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

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32g0xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define OSC32_IN_Pin GPIO_PIN_14
#define OSC32_IN_GPIO_Port GPIOC
#define OSC32_OUT_Pin GPIO_PIN_15
#define OSC32_OUT_GPIO_Port GPIOC
#define LOG_TX_Pin GPIO_PIN_2
#define LOG_TX_GPIO_Port GPIOA
#define PD_ADC_Pin GPIO_PIN_3
#define PD_ADC_GPIO_Port GPIOA
#define LCD_RST_Pin GPIO_PIN_1
#define LCD_RST_GPIO_Port GPIOB
#define DROP_INT_Pin GPIO_PIN_10
#define DROP_INT_GPIO_Port GPIOB
#define DROP_INT_EXTI_IRQn EXTI4_15_IRQn
#define BOOST_MODE_CTRL_Pin GPIO_PIN_12
#define BOOST_MODE_CTRL_GPIO_Port GPIOB
#define BTN_MINUS_Pin GPIO_PIN_6
#define BTN_MINUS_GPIO_Port GPIOB
#define BTN_PLUS_Pin GPIO_PIN_7
#define BTN_PLUS_GPIO_Port GPIOB
#define BTN_MODE_Pin GPIO_PIN_8
#define BTN_MODE_GPIO_Port GPIOB
#define BTN_MUTE_Pin GPIO_PIN_9
#define BTN_MUTE_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
