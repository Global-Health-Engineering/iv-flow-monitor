/*
   ___  ___  _______  ______________
  / _ \/ _ \/  _/ _ \/  _/_  __/ __ \
 / // / , _// // ___// /  / / / /_/ /
/____/_/|_/___/_/  /___/ /_/  \____/

DRIPITO – A bachelor's thesis by Leandro Catarci
-------------------------------------------------
Drop‑rate logger for gravity IV lines – *application layer*

This unit **does not** contain `main()`.  It is intended to be linked
alongside the STM32Cube‑generated startup file (`Core/Src/main.c`).
Cube takes care of clocks and peripheral initialisation; **Dripito_Init()**
prints the splash, starts the log and leaves all drop detection to the
EXTI ISR below.

Build target: STM32G030C6 (LoRa Drop‑Meter board, rev‑B)
License: MIT
*/

#include "main.h"
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <inttypes.h>

/* ------------------------------------------------------------------------- */
/*                              CONFIGURATION                                */
/* ------------------------------------------------------------------------- */
#define DRIP_FACTOR_GTT_PER_ML  20   /* 20 gtt = 1 mL (paediatric set) */
#define BATTERY_FULL_MV        4200  /* Li‑ion full                    */
#define BATTERY_EMPTY_MV       3300  /* cutoff 0%                      */

/* ------------------------------------------------------------------------- */
/*                         GLOBAL STATE & HANDLES                            */
/* ------------------------------------------------------------------------- */
extern ADC_HandleTypeDef   hadc1;
extern RTC_HandleTypeDef   hrtc;
extern TIM_HandleTypeDef   htim1;
extern UART_HandleTypeDef  huart2;

static volatile uint32_t drop_count      = 0;
static volatile uint32_t last_drop_tick  = 0; /* ms */
static volatile uint32_t total_volume_ul = 0; /* µL */

static uint32_t boot_tick_ms = 0;            /* HAL_GetTick at Dripito_Init */

/* ------------------------------------------------------------------------- */
/*                         PUBLIC ENTRY POINTS                               */
/* ------------------------------------------------------------------------- */
void    Dripito_Init(void);           /* called once from Cube main() */
void    buzzer_startup_jingle(void);  /* optional: can be reused elsewhere */

/* ------------------------------------------------------------------------- */
/*                            FORWARD DECLARATIONS                           */
/* ------------------------------------------------------------------------- */
static void splash_print(void);
static void log_header_print(void);
static void log_row_print(uint32_t dt_ms);
static uint16_t read_battery_mv(void);
static uint8_t  battery_pct(uint16_t mv);
static void     buzzer_set_duty(uint16_t duty);
static void     buzzer_play(uint16_t freq_hz, uint16_t dur_ms);

/* ------------------------------------------------------------------------- */
/*                          HARDWARE CALLBACKS                               */
/* ------------------------------------------------------------------------- */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == DROP_INT_Pin) {
        uint32_t now = HAL_GetTick();
        uint32_t dt  = now - last_drop_tick;            /* ms since previous */
        last_drop_tick = now;

        drop_count++;
        total_volume_ul += (1000U / DRIP_FACTOR_GTT_PER_ML); /* µL per drop */

        log_row_print(dt);
    }
}

/* ------------------------------------------------------------------------- */
/*                              INITIALISATION                               */
/* ------------------------------------------------------------------------- */
void Dripito_Init(void)
{
    /* Optional audible start‑up */
    buzzer_startup_jingle();

    /* Time zero for elapsed‑time column */
    boot_tick_ms = HAL_GetTick();

    /* User feedback */
    splash_print();
    log_header_print();
}

/* ------------------------------------------------------------------------- */
/*                              PRINT HELPERS                                */
/* ------------------------------------------------------------------------- */
static void splash_print(void)
{
    printf("\r\n   ___  ___  _______  ______________ \r\n");
    printf("  / _ \\/ _ \\/  _/ _ \\/  _/_  __/ __ \\r\n");
    printf(" / // / , _// // ___// /  / / / /_/ /\r\n");
    printf("/____/_/|_/___/_/  /___/ /_/  \\____/ \r\n\r\n");
    printf("DRIPITO – A bachelor's thesis by Leandro Catarci\r\n\r\n");
}

static void log_header_print(void)
{
    printf("DROP# | dt[ms] | Rate[ml/h] (drops/min) | Total[ml] | Elapsed[min] | Batt[%%]\r\n");
    printf("-----+--------+------------------------+-----------+-------------+--------\r\n");
}

static void log_row_print(uint32_t dt_ms)
{
    /* integer‑only maths – no _printf_float needed */
    uint32_t dpm        = (dt_ms > 0U) ? (60000U / dt_ms) : 0U;           /* drops/min  */
    uint32_t ml_h       = (dpm * 60U) / DRIP_FACTOR_GTT_PER_ML;           /* mL/h       */
    uint32_t ml_total   = total_volume_ul / 1000U;                        /* mL total   */
    uint32_t elapsed_m  = (HAL_GetTick() - boot_tick_ms) / 60000U;        /* minutes    */

    uint16_t batt_mv    = read_battery_mv();
    uint8_t  batt_pct_v = battery_pct(batt_mv);

    printf("%5"PRIu32" | %6"PRIu32" | %10"PRIu32" (%5"PRIu32") | %9"PRIu32" | %11"PRIu32" | %3u%%\r\n",
           drop_count, dt_ms, ml_h, dpm, ml_total, elapsed_m, batt_pct_v);
}

/* ------------------------------------------------------------------------- */
/*                              BATTERY HELPERS                              */
/* ------------------------------------------------------------------------- */
static uint16_t read_battery_mv(void)
{
    extern uint32_t Read_Battery_mV(void);  /* defined in adc helpers */
    return (uint16_t)Read_Battery_mV();
}

static uint8_t battery_pct(uint16_t mv)
{
    if (mv >= BATTERY_FULL_MV)  return 100U;
    if (mv <= BATTERY_EMPTY_MV) return 0U;
    return (uint8_t)(((uint32_t)(mv - BATTERY_EMPTY_MV) * 100U) /
                     (BATTERY_FULL_MV - BATTERY_EMPTY_MV));
}

/* ------------------------------------------------------------------------- */
/*                          BUZZER START‑UP JINGLE                           */
/* ------------------------------------------------------------------------- */
static void buzzer_set_duty(uint16_t duty)
{
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, duty);
}

static void buzzer_play(uint16_t freq_hz, uint16_t dur_ms)
{
    uint32_t timer_clk = 1000000U;                 /* TIM1 clock after prescaler */
    uint32_t period    = timer_clk / freq_hz;
    __HAL_TIM_SET_AUTORELOAD(&htim1, period - 1U);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, period / 2U); /* 50 % duty */
    HAL_Delay(dur_ms);
    buzzer_set_duty(0);
}

void buzzer_startup_jingle(void)
{
    for (uint16_t f = 3000U; f <= 4000U; f += 100U) {
        buzzer_play(f, 30U);
        HAL_Delay(20U);
    }
}
