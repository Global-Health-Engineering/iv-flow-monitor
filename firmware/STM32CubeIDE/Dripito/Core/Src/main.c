/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
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
#include "lcd.h"
#include "buzzer.h"
#include "buttons.h"
#include <stdio.h>
#include <math.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* Phase 1 dual-beam drop-detection demo */
#define BEAM_PITCH_MM     10.0f       /* TOP-to-BOT optical centre-to-centre */
#define G_MMPS2           9810.0f     /* gravitational acceleration, mm/s^2  */
#define BEAM_WIDTH_MM     0.0f        /* 2026-05-13 bench: W=5 over-corrected (chord ~2 ms at v~1 m/s
                                          → d_mm negative for every drop, 100% DROP_REJECT d_low).
                                          Reverted to design-doc placeholder W=0 (point-beam approx);
                                          true W to be back-solved offline from gravimetric data. */
#define V_CAL_K           1.27f       /* 2026-05-13 bench: scalar correction applied to vol_uL after
                                          the chord-to-sphere conversion. Derived as the unweighted
                                          mean of per-run k = V_true_gravimetric / V_est across the
                                          four 2026-05-13 campaigns (V_50_01..04): k = (1.61, 1.00,
                                          1.32, 1.13). Compensates for the residual chord-vs-volume
                                          gap left by drop oscillation between oblate and prolate
                                          shape during free fall, which the mean-pulse algorithm
                                          cannot resolve per-drop. Per-run residual after correction
                                          is ~30% — calibrate per drip-set + fluid combination at
                                          deployment for tighter performance. */

/* Per-channel hysteretic edge thresholds are *calibrated at boot*: see
   the cal block right after the splash. Clear baselines drift between
   boards (2026-05-08 bench: TOP ~3100, BOT ~3280, both noisy) so a
   self-cal is more robust than fixed values. Both channels saturate
   at 4094 when blocked, so plenty of headroom.                             */
#define CAL_DURATION_MS   250U        /* sample baseline this long at boot   */
#define CAL_MARGIN_LOW     30U        /* thresh_low  = max_baseline + this. 2026-05-13 bench:
                                          dropped from 80 → 30 so the drop's signal tail stays above
                                          threshold longer, extending tau toward the geometric chord.
                                          Trade-off: less margin against baseline noise. */
#define CAL_MARGIN_HIGH   100U        /* thresh_high = max_baseline + this. 2026-05-13 bench:
                                          dropped from 220 → 100. The high-position experiment with
                                          margin=30 confirmed that lowering the threshold catches a
                                          long BOT splash tail (BOT/TOP pulse ratio jumped from 2x to
                                          7.8x), so we keep margin=100 to clip the splash artifact
                                          and rely on V_CAL_K to correct the remaining bias. */

#define REARM_CLEAR_MS    150U        /* both channels clear this long → re-arm */

/* Step 6 — session calibration: collect CAL_N drops, trim min and max,
   average the middle 8 → V_cal. Tate's Law makes drop diameter roughly
   constant per (fluid × outlet), so 8 trimmed samples is enough to lock
   the per-drop volume for the rest of the session. */
#define CAL_N             10U
#define CAL_TRIM_LO        1U         /* drop smallest CAL_TRIM_LO sample(s) */
#define CAL_TRIM_HI        1U         /* drop largest  CAL_TRIM_HI sample(s) */

/* Flow-rate window (Q = drops_in_window · V_cal / window). 30 s captures
   ~3 drops at 20 mL/h and ~17 drops at 100 mL/h with a macro-20 set. */
#define WINDOW_MS         30000U
#define MAX_TRACKED_DROPS 32U         /* ring buffer of drop timestamps      */

/* Physical sanity guards on a candidate drop. Below these floors / above
   the ceiling the drop is silently rejected — keeps optical glitches,
   misalignment, and gravity-corrected v_TOP sign flips out of v_samples
   and the rolling Q. Numbers chosen with margin around real macro-10 /
   macro-15 / macro-20 / pediatric-60 drip-set drops. */
#define V_MMPS_MIN         50.0f      /* < 50 mm/s ≈ unphysical for free fall */
#define D_MM_MIN            0.1f      /* 2026-05-13 bench: relaxed from 1.0 → 0.1 so chord-time-
                                          truncated drops still propagate to the CSV. Bench observed
                                          tau ~1 ms at v ~0.73 m/s → d ~0.7 mm (rejected at 1.0),
                                          even though the underlying physical drops are macro-set.
                                          Treat sub-mm reports as a signal of the truncation effect,
                                          not as a noise rejection failure. */
#define VOL_UL_MAX        500.0f      /* > 500 µL is bigger than any drop set  */

/* Alarm policy (IEC 60601-2-24 / NICE CG174 spirit). Armed against the
   instantaneous Q at the moment of arm; ±WARN_PCT triggers a slow tick,
   ±ALARM_PCT triggers a fast triple-beep. NO_DROP_TIMEOUT catches a
   stopped drip (occluded line, empty bag). MUTE silences for a fixed
   window then re-evaluates. */
#define WARN_PCT             15U
#define ALARM_PCT            25U
#define NO_DROP_TIMEOUT_MS 15000U
#define MUTE_DURATION_MS   60000U

/* Buzzer cadence. Tone Hz pulled apart from LED ARR so the boost ARR
   restore inside buzzer.c always lands cleanly. */
#define WARN_BEEP_HZ        1800U
#define WARN_BEEP_ON_MS      250U
#define WARN_BEEP_OFF_MS    3000U
#define ALARM_BEEP_HZ       2500U
#define ALARM_BEEP_ON_MS     100U
#define ALARM_BEEP_OFF_MS    180U     /* 4 Hz at the alarm rate */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;

COMP_HandleTypeDef hcomp1;

LPTIM_HandleTypeDef hlptim1;

SPI_HandleTypeDef hspi1;

TIM_HandleTypeDef htim1;

UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */

/* SWD-readable debug log. The host reads `dbg_log` over SWD (Hotplug
   mode, no halt) and emits new entries to stdout. Buffer is monotonic
   `head` + 32-slot ring of NUL-terminated strings. Reader script:
   firmware/STM32CubeIDE/Dripito/tools/read_swd_log.py */
#define DBG_LOG_SLOTS    32U
#define DBG_LOG_SLOT_B   48U
typedef struct {
  uint32_t magic;                                          /* 0xD11D0001  */
  volatile uint32_t head;                                  /* total writes */
  char     slots[DBG_LOG_SLOTS][DBG_LOG_SLOT_B];
} dbg_log_t;
dbg_log_t dbg_log __attribute__((used)) = { .magic = 0xD11D0001U };

/* Blocking UART byte-stream. ~87 us per byte at 115200,8N1; an 80-byte
   line is ~7 ms blocked, which we tolerate because drop events are
   ≤ a few per second and the SWD log + LCD update around the same site
   already cost similar order. Skips silently if HAL returns busy/error
   — UART output is observability, not load-bearing.
   Diag: total bytes sent and last-error code are exported in
   `uart_diag` for SWD inspection. */
typedef struct {
  uint32_t magic;
  uint32_t bytes_sent;
  uint32_t call_count;
  uint32_t last_status;     /* HAL_StatusTypeDef */
  uint32_t last_err_code;   /* huart1.ErrorCode */
} uart_diag_t;
uart_diag_t uart_diag __attribute__((used)) = { .magic = 0xD11D0002U };

static void uart_send(const char *s, uint16_t len)
{
  HAL_StatusTypeDef st = HAL_UART_Transmit(&huart1, (uint8_t *)s, len, 50U);
  uart_diag.call_count++;
  uart_diag.last_status = (uint32_t)st;
  uart_diag.last_err_code = huart1.ErrorCode;
  if (st == HAL_OK) {
    uart_diag.bytes_sent += len;
  }
}

static void uart_send_str(const char *s)
{
  uint16_t n = 0U;
  while (s[n] != '\0' && n < 200U) n++;
  uart_send(s, n);
}

static void log_msg(const char *s)
{
  /* Write to SWD ring buffer (always available, even without UART). */
  uint32_t h    = dbg_log.head;
  uint32_t slot = h % DBG_LOG_SLOTS;
  uint32_t i    = 0U;
  while (i < (DBG_LOG_SLOT_B - 1U) && s[i] != '\0') {
    dbg_log.slots[slot][i] = s[i];
    i++;
  }
  dbg_log.slots[slot][i] = '\0';
  __DMB();
  dbg_log.head = h + 1U;

  /* Mirror to UART as a CSV event line: EVT,<t_ms>,<message> */
  char buf[80];
  int n = snprintf(buf, sizeof(buf), "EVT,%lu,%s\r\n",
                   (unsigned long)HAL_GetTick(), s);
  if (n > 0) {
    if (n > (int)sizeof(buf)) n = (int)sizeof(buf);
    uart_send(buf, (uint16_t)n);
  }
}

/* Per-drop CSV row in a richer schema than the 48-byte SWD slot allows.
   Columns: DROP,<t_ms>,<drop_N>,<transit_us>,<pulse_top_us>,<pulse_bot_us>,
            <v_cmps>,<d_0.1mm>,<V_0.1uL>,<state>,<Q_0.01mLph>,<top_raw>,<bot_raw>
   First five data columns (after the DROP marker) map directly to the
   load_run.py schema (abs_ms, drop_N, transit_us, pulse_top_us,
   pulse_bot_us); the remaining columns are firmware-side derived
   quantities + raw ADC at edge-in for downstream sanity checks.
   state: 1=CAL, 2=METER. Q is the rolling flow rate at this drop (0 in CAL). */
static void log_drop_csv(uint32_t t_ms, uint32_t drop_n,
                         uint32_t transit_us,
                         uint32_t pulse_top_us, uint32_t pulse_bot_us,
                         int32_t v_cmps, int32_t d_tenths, int32_t vol_tenths,
                         int state_int, int32_t Q_cmLph,
                         uint16_t top_raw, uint16_t bot_raw)
{
  char buf[140];
  int n = snprintf(buf, sizeof(buf),
                   "DROP,%lu,%lu,%lu,%lu,%lu,%ld,%ld,%ld,%d,%ld,%u,%u\r\n",
                   (unsigned long)t_ms, (unsigned long)drop_n,
                   (unsigned long)transit_us,
                   (unsigned long)pulse_top_us,
                   (unsigned long)pulse_bot_us,
                   (long)v_cmps, (long)d_tenths, (long)vol_tenths,
                   state_int, (long)Q_cmLph,
                   (unsigned)top_raw, (unsigned)bot_raw);
  if (n > 0) {
    if (n > (int)sizeof(buf)) n = (int)sizeof(buf);
    uart_send(buf, (uint16_t)n);
  }
}

/* Reject reason for a drop candidate that the physical-sanity guards
   filtered out. Emitted as an EVT line so it's visible on UART without
   polluting the DROP CSV stream:

     EVT,<t_ms>,DROP_REJECT,reason=<r>,dt_us=<dt>,tau_us=<tau>,
         v_mmps_tenths=<v>,d_mm_tenths=<d>,V_uL_tenths=<V>

   Reasons:
     "fast"   — dt_us <= 500 or tau_us <= 100 (pre-physics first-pass guard)
     "v_low"  — gravity-corrected v_TOP below V_MMPS_MIN (pen waves land here)
     "d_low"  — derived diameter below D_MM_MIN
     "vol_neg"— derived volume <= 0
     "vol_hi" — derived volume > VOL_UL_MAX */
static void log_drop_reject(uint32_t t_ms, const char *reason,
                            uint32_t dt_us, uint32_t tau_us,
                            float v_mmps, float d_mm, float vol_uL)
{
  char buf[140];
  int v_t = (int)(v_mmps * 10.0f + (v_mmps >= 0 ? 0.5f : -0.5f));
  int d_t = (int)(d_mm   * 10.0f + (d_mm   >= 0 ? 0.5f : -0.5f));
  int V_t = (int)(vol_uL * 10.0f + (vol_uL >= 0 ? 0.5f : -0.5f));
  int n = snprintf(buf, sizeof(buf),
                   "EVT,%lu,DROP_REJECT,reason=%s,dt_us=%lu,tau_us=%lu,"
                   "v_mmps_tenths=%d,d_mm_tenths=%d,V_uL_tenths=%d\r\n",
                   (unsigned long)t_ms, reason,
                   (unsigned long)dt_us, (unsigned long)tau_us,
                   v_t, d_t, V_t);
  if (n > 0) {
    if (n > (int)sizeof(buf)) n = (int)sizeof(buf);
    uart_send(buf, (uint16_t)n);
  }
}

/* Last completed drop, in display-ready integer fixed-point. Survives view
   switches so toggling between DROP / FLOW / RAW always shows the most
   recent measurement until the next drop arrives. */
typedef struct {
  uint32_t dt_us;       /* inter-beam transit  tB_in − tT_in   */
  uint32_t tau_us;      /* TOP shadow          tT_out − tT_in  */
  int32_t  v_centi_mps; /* gravity-corrected v_TOP in 0.01 m/s */
  int32_t  d_tenths;    /* drop diameter in 0.1 mm             */
  int32_t  vol_tenths;  /* drop volume   in 0.1 µL             */
  uint8_t  valid;       /* 0 = no drop yet / last one rejected */
} drop_metrics_t;

typedef enum { STATE_CAL = 0, STATE_METER } session_state_t;
typedef enum { VIEW_DROP = 0, VIEW_FLOW, VIEW_RAW, VIEW_COUNT } view_t;
typedef enum { ALARM_NONE = 0, ALARM_WARN, ALARM_FIRE } alarm_level_t;

static drop_metrics_t   last_drop      = {0};
static float            v_samples[CAL_N];
static uint8_t          v_count        = 0;
static float            v_cal_uL       = 0.0f;
static session_state_t  session_state  = STATE_CAL;

static uint32_t         drop_times_ms[MAX_TRACKED_DROPS];
static uint8_t          drop_head      = 0;   /* next-write index            */
static uint8_t          drop_total     = 0;   /* saturates at MAX_TRACKED    */
static uint32_t         drops_accepted = 0;   /* monotonic accepted-drop counter,
                                                 logged as drop_N in DROP rows */

static view_t           view           = VIEW_DROP;
static uint8_t          view_dirty     = 1;

/* Alarm-arm state — orthogonal to session_state. Only meaningful once
   the session has calibrated (STATE_METER) and a valid Q exists. */
static uint8_t          alarm_armed    = 0;
static float            target_Q_mLph  = 0.0f;
static alarm_level_t    alarm_level    = ALARM_NONE;
static uint32_t         mute_until_ms  = 0;
static uint32_t         next_beep_ms   = 0;
static uint8_t          beep_on        = 0;
static uint32_t         last_drop_ms   = 0;   /* updated on every kept drop  */

/* UART RX command-line buffer. Polled at the top of the main loop;
   accumulates printable bytes until '\r' or '\n' triggers parsing. */
#define CMD_BUF_SZ 80U
static char     cmd_buf[CMD_BUF_SZ];
static uint8_t  cmd_len = 0U;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_ADC1_Init(void);
static void MX_COMP1_Init(void);
static void MX_SPI1_Init(void);
static void MX_LPTIM1_Init(void);
static void MX_TIM1_Init(void);
static void MX_USART1_UART_Init(void);
/* USER CODE BEGIN PFP */
static uint16_t adc_read(uint32_t channel);
static void lcd_put_at(uint8_t line, uint8_t col, char c);
static void lcd_line_padded(uint8_t line, const char *s);
static void render_drop(void);
static void render_flow(uint32_t now_ms);
static void render_raw(uint16_t top_raw, uint16_t bot_raw,
                       uint16_t top_hi, uint16_t bot_hi,
                       uint8_t top_in, uint8_t bot_in,
                       uint8_t armed, uint8_t seq_ok);
static float compute_Q_mLph(uint32_t now_ms);
static uint32_t interp_edge_us(uint16_t v_prev, uint32_t t_prev_us,
                               uint16_t v_now,  uint32_t t_now_us,
                               uint16_t v_threshold);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

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
  __HAL_RCC_SYSCFG_CLK_ENABLE();
    SYSCFG->CFGR1 |= SYSCFG_CFGR1_PA11_RMP |
    SYSCFG_CFGR1_PA12_RMP;
  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_ADC1_Init();
  MX_COMP1_Init();
  MX_SPI1_Init();
  MX_LPTIM1_Init();
  MX_TIM1_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);   /* buzzer on PA8   */
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2);   /* LED_TOP on PB3  */
  HAL_GPIO_WritePin(LED_CTRL_BOT_GPIO_Port, LED_CTRL_BOT_Pin, GPIO_PIN_SET);
  __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, 250);  /* 100% duty LED_TOP (compare > ARR=249) */

  /* Free-running 1 MHz µs counter on TIM2 (32-bit), used for drop-event
     timestamps. Independent of TIM1 so buzzer tones don't disturb timing.   */
  __HAL_RCC_TIM2_CLK_ENABLE();
  TIM2->PSC = (SystemCoreClock / 1000000U) - 1U;
  TIM2->ARR = 0xFFFFFFFFU;
  TIM2->EGR = TIM_EGR_UG;
  TIM2->CR1 = TIM_CR1_CEN;

  HAL_ADCEx_Calibration_Start(&hadc1);
  /* Bump common sampling time to 160.5 cycles (~5 µs) so VREFINT and
     TEMPSENSOR settle. .ioc default of 1.5 cycles is too fast for them.   */
  MODIFY_REG(ADC1->SMPR, ADC_SMPR_SMP1, ADC_SAMPLETIME_160CYCLES_5);

  LCD_Init();
  LCD_Clear();

  /* Phase 1: 5 drops fall in sequence, accumulating into the logo on
     line 3. Order: middle (7), far left (3), far right (11), 5, 9.
     Twice as fast as before (~1.1 s).                                   */
  {
    static const uint8_t drop_cols[5] = {7, 3, 11, 5, 9};
    for (int d = 0; d < 5; ++d) {
      uint8_t col = drop_cols[d];
      lcd_put_at(0, col, '.'); HAL_Delay(60);
      lcd_put_at(0, col, ' ');
      lcd_put_at(1, col, 'o'); HAL_Delay(60);
      lcd_put_at(1, col, ' ');
      lcd_put_at(2, col, 'O'); HAL_Delay(60);
      lcd_put_at(2, col, ' ');
      lcd_put_at(3, col, '*');
      /* "plip" on landing: quick tick + short ring-down */
      Buzzer_PlayFreq(2800, 5);
      Buzzer_PlayFreq(1500, 12);
      HAL_Delay(23);
    }
    HAL_Delay(125);   /* let the row of drops register as a logo */
  }

  /* Phase 2: type all four lines column-by-column, left-to-right (~0.3 s).
     Overwrites the row of drops on line 3 with the title block.         */
  {
    static const char *const L[4] = {
      "Dripito Rev-B   ",
      "ETH GHE 2026    ",
      "Pediatric IV    ",
      "Flow Monitor    ",
    };
    for (int col = 0; col < 16; ++col) {
      for (int ln = 0; ln < 4; ++ln) {
        lcd_put_at((uint8_t)ln, (uint8_t)col, L[ln][col]);
      }
      HAL_Delay(16);
    }
  }

  /* Phase 3: hold the text for 1 s, boot chime up front. */
  Buzzer_PlayFreq(1319, 50);   /* E6 */
  HAL_Delay(15);
  Buzzer_PlayFreq(1976, 100);  /* B6 */
  HAL_Delay(850);
  LCD_Clear();
  /* USER CODE END 2 */

  /* Boot-time auto-calibration: sample both photodiode chains for
     CAL_DURATION_MS while the chamber is empty, take the worst-case
     ceiling on each channel, and set hysteretic thresholds above it.
     Adapts to per-board variation, ambient drift, and casing tolerance. */
  LCD_Print(0, "Calibrating...  ");
  LCD_Print(1, "                ");
  LCD_Print(2, "                ");
  LCD_Print(3, "Hold off chamber");

  uint16_t top_max = 0, bot_max = 0;
  uint32_t cal_end = HAL_GetTick() + CAL_DURATION_MS;
  while ((int32_t)(cal_end - HAL_GetTick()) > 0) {
    uint16_t t = adc_read(ADC_CHANNEL_1);
    uint16_t b = adc_read(ADC_CHANNEL_4);
    if (t > top_max) top_max = t;
    if (b > bot_max) bot_max = b;
  }

  uint16_t top_thresh_low  = (uint16_t)(top_max + CAL_MARGIN_LOW);
  uint16_t top_thresh_high = (uint16_t)(top_max + CAL_MARGIN_HIGH);
  uint16_t bot_thresh_low  = (uint16_t)(bot_max + CAL_MARGIN_LOW);
  uint16_t bot_thresh_high = (uint16_t)(bot_max + CAL_MARGIN_HIGH);

  /* Briefly show the calibrated ceilings so they can be sanity-checked. */
  {
    char line[24];
    snprintf(line, sizeof(line), "Cal T:%4u B:%4u", top_max, bot_max);
    LCD_Print(0, line);
    HAL_Delay(700);
    /* UART schema preamble so the host parser knows what's coming. */
    uart_send_str("\r\n# Dripito Rev-B UART log v1; t_ms = ms since boot\r\n");
    uart_send_str("# EVT,<t_ms>,<message>\r\n");
    uart_send_str("# DROP,<t_ms>,<drop_N>,<transit_us>,<pulse_top_us>,<pulse_bot_us>,"
                  "<v_centi_mps>,<d_0.1mm>,<V_0.1uL>,<state>,<Q_0.01mLph>,"
                  "<top_raw>,<bot_raw>\r\n");
    uart_send_str("# EVT,<t_ms>,DROP_REJECT,reason=<r>,dt_us=...,tau_us=...,"
                  "v_mmps_tenths=...,d_mm_tenths=...,V_uL_tenths=...\r\n");
    log_msg("BOOT done");
    char tmp[48];
    snprintf(tmp, sizeof(tmp), "thresh T_hi=%u B_hi=%u",
             (unsigned)top_thresh_high, (unsigned)bot_thresh_high);
    log_msg(tmp);
  }
  LCD_Clear();

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  /* Phase 1: dual-beam drop detection.
     Each drop produces four edges in order:
       tT_in  — leading edge enters TOP beam (ADC rises above TOP_THRESH_HIGH)
       tT_out — trailing edge exits TOP    (ADC falls below TOP_THRESH_LOW)
       tB_in  — leading edge enters BOT    (ADC rises above BOT_THRESH_HIGH)
       tB_out — trailing edge exits BOT    (ADC falls below BOT_THRESH_LOW)

     Edge timestamps are interpolated between the two ADC samples that
     bracketed the threshold crossing — this pushes the timing precision
     from the loop period (~30 µs) down toward the ADC noise floor and
     keeps V_drop variance below 1 % at typical drip-set rates.

     Math:
       Δt   = tB_in − tT_in
       τTOP = tT_out − tT_in
       v_TOP = L/Δt − ½ g · Δt        (gravity-corrected)
       chord = v_TOP · τ + ½ g · τ²   (gravity-corrected, mirrors Δt treatment)
       d     = chord − W_beam         (drop diameter; W_beam = bench value)
       V   = (π/6) · d^3              (spherical-drop assumption)
     Session: first CAL_N drops feed v_samples → trimmed mean = V_cal,
     then STATE_METER displays a rolling flow rate Q = N·V_cal/window.

     Buttons (left → right on the front plate):
       MODE  → cycle view (DROP → FLOW → RAW → DROP …)
       RES   → toggle alarm-arm   (locks Q_target = current Q)
       MUTE  → silence alarm for MUTE_DURATION_MS

     Phase 2 (LPTIM1-pulsed LED + COMP1 wake-from-STOP single-µA counter)
     is deferred — peripherals are initialized but unused; staying in
     active polling until validation campaign closes.                         */
  uint8_t  top_in        = 0;
  uint8_t  bot_in        = 0;
  uint32_t tT_in         = 0;
  uint32_t tT_out        = 0;
  uint32_t tB_in         = 0;
  uint32_t tB_out        = 0;
  uint16_t top_raw_at_in = 0;   /* ADC reading captured at TOP_in edge — logged */
  uint16_t bot_raw_at_in = 0;   /* ADC reading captured at BOT_in edge — logged */
  uint8_t  drop_armed    = 0;   /* edge-detector re-arm latch (≠ alarm_armed) */
  uint8_t  top_seq_ok    = 0;
  uint32_t both_clear_ms = 0;
  uint32_t last_periodic_ms = 0;

  /* Previous-sample state for sub-sample edge interpolation. Seeded with
     the latest threshold so the very first sample's "previous" doesn't
     spurious-trigger; subsequent updates happen at end of each loop. */
  uint16_t prev_top_raw = 0;
  uint16_t prev_bot_raw = 0;
  uint32_t prev_top_us  = 0;
  uint32_t prev_bot_us  = 0;

  while (1)
  {
    /* USER CODE END WHILE */
    Buttons_Poll();
    /* USER CODE BEGIN 3 */

    uint32_t now_ms = HAL_GetTick();

    /* --- UART RX command interface (bench-time tooling) ---
       Polled byte-by-byte from the USART RDR (no interrupts, no DMA).
       Commands are line-terminated (\r or \n); responses begin with '<'
       so the host parser can distinguish them from streamed DROP / EVT
       lines.

         PING                  → <PONG,uptime_ms=...
         STATE                 → runtime state dump (thresholds, armed,
                                 session, drops_accepted, view, uptime)
         SIM_DROP dt tau bot   → run the accept/reject math on the given
                                 (dt_us, tau_us, pulse_bot_us) without
                                 touching session_state, v_samples, or
                                 drop_times_ms. Emits a DROP line with
                                 drop_N=0 and state=0 to flag it as SIM,
                                 or an EVT,DROP_REJECT if guards fire.
         HELP                  → list commands                              */
    while (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_RXNE)) {
      uint8_t rx = (uint8_t)(huart1.Instance->RDR & 0xFFU);
      if (rx == '\r' || rx == '\n') {
        if (cmd_len > 0U) {
          cmd_buf[cmd_len] = '\0';
          if (strncmp(cmd_buf, "PING", 4) == 0) {
            char resp[40];
            int n = snprintf(resp, sizeof(resp),
                             "<PONG,uptime_ms=%lu\r\n",
                             (unsigned long)now_ms);
            if (n > 0) uart_send(resp, (uint16_t)n);
          } else if (strncmp(cmd_buf, "STATE", 5) == 0) {
            char resp[180];
            const char *sname = (session_state == STATE_CAL) ? "CAL" : "METER";
            const char *vname = (view == VIEW_DROP) ? "DROP"
                              : (view == VIEW_FLOW) ? "FLOW" : "RAW";
            int n = snprintf(resp, sizeof(resp),
                "<STATE,thresh_T_hi=%u,thresh_B_hi=%u,armed=%u,seq_ok=%u,"
                "session=%s,v_count=%u,drops_acc=%lu,view=%s,uptime_ms=%lu\r\n",
                (unsigned)top_thresh_high, (unsigned)bot_thresh_high,
                (unsigned)drop_armed, (unsigned)top_seq_ok,
                sname, (unsigned)v_count,
                (unsigned long)drops_accepted, vname,
                (unsigned long)now_ms);
            if (n > 0) uart_send(resp, (uint16_t)n);
          } else if (strncmp(cmd_buf, "SIM_DROP", 8) == 0) {
            /* Manual u32 parser — three space-separated decimals after
               the command keyword. Avoids pulling in sscanf. */
            const char *p = cmd_buf + 8;
            uint32_t dt_us = 0U, tau_us = 0U, pulse_bot_us = 0U;
            uint8_t parse_ok = 1U;
            for (uint8_t arg = 0U; arg < 3U; ++arg) {
              while (*p == ' ' || *p == '\t') p++;
              if (*p < '0' || *p > '9') { parse_ok = 0U; break; }
              uint32_t v = 0U;
              while (*p >= '0' && *p <= '9') {
                v = v * 10U + (uint32_t)(*p - '0');
                p++;
              }
              if      (arg == 0U) dt_us        = v;
              else if (arg == 1U) tau_us       = v;
              else                pulse_bot_us = v;
            }
            if (!parse_ok) {
              uart_send_str("<ERR,SIM_DROP needs 3 uint args: dt_us tau_us pulse_bot_us\r\n");
            } else {
              uart_send_str("<SIM_DROP_ACK\r\n");
              if (dt_us <= 500U || tau_us <= 100U) {
                log_drop_reject(now_ms, "fast", dt_us, tau_us, 0.0f, 0.0f, 0.0f);
              } else {
                float dt_s     = (float)dt_us  * 1.0e-6f;
                float tau_s    = (float)tau_us * 1.0e-6f;
                float v_mmps   = (BEAM_PITCH_MM / dt_s) - 0.5f * G_MMPS2 * dt_s;
                float chord_mm = v_mmps * tau_s + 0.5f * G_MMPS2 * tau_s * tau_s;
                float d_mm     = chord_mm - BEAM_WIDTH_MM;
                float vol_uL   = (3.14159265f / 6.0f * d_mm * d_mm * d_mm) * V_CAL_K;
                uint8_t accept = (v_mmps  >= V_MMPS_MIN)
                              && (d_mm    >= D_MM_MIN)
                              && (vol_uL  >  0.0f)
                              && (vol_uL  <= VOL_UL_MAX);
                if (accept) {
                  int32_t v_cmps     = (int32_t)(v_mmps  * 0.1f  + 0.5f);
                  int32_t d_tenths   = (int32_t)(d_mm    * 10.0f + 0.5f);
                  int32_t vol_tenths = (int32_t)(vol_uL  * 10.0f + 0.5f);
                  /* drop_N=0 and state=0 flag this row as SIM, not bench. */
                  log_drop_csv(now_ms, 0U,
                               dt_us, tau_us, pulse_bot_us,
                               v_cmps, d_tenths, vol_tenths,
                               0, 0,           /* state=0 (SIM), Q=0 */
                               0U, 0U);        /* raw ADC unused for SIM */
                } else {
                  const char *r = (v_mmps  < V_MMPS_MIN) ? "v_low"
                                : (d_mm    < D_MM_MIN  ) ? "d_low"
                                : (vol_uL <= 0.0f      ) ? "vol_neg"
                                :                          "vol_hi";
                  log_drop_reject(now_ms, r, dt_us, tau_us,
                                  v_mmps, d_mm, vol_uL);
                }
              }
            }
          } else if (strncmp(cmd_buf, "HELP", 4) == 0) {
            uart_send_str("<HELP,PING|STATE|SIM_DROP <dt_us> <tau_us> <pulse_bot_us>|HELP\r\n");
          } else {
            uart_send_str("<ERR,unknown command (try HELP)\r\n");
          }
        }
        cmd_len = 0U;
      } else if (rx >= 0x20 && rx < 0x7F && cmd_len < (CMD_BUF_SZ - 1U)) {
        cmd_buf[cmd_len++] = (char)rx;
      }
    }

    /* --- Button bindings ---
       MODE = left button = cycle view forward.
       RES  = middle      = arm / disarm against current Q.
       MUTE = right       = silence active alarm for MUTE_DURATION_MS. */
    /* MODE: short tap = cycle view; long hold (>=700 ms) = arm / disarm
       against the current Q. RES button is unpopulated on this board so
       the arm action moved to MODE-long. */
    if (Buttons_ModePressed()) {
      view = (view_t)(((unsigned)view + 1U) % (unsigned)VIEW_COUNT);
      view_dirty = 1;
      const char *vname = (view == VIEW_DROP) ? "DROP"
                        : (view == VIEW_FLOW) ? "FLOW" : "RAW";
      char tmp[32];
      snprintf(tmp, sizeof(tmp), "BTN MODE view=%s", vname);
      log_msg(tmp);
    }

    if (Buttons_ModeLongPressed()) {
      if (session_state == STATE_METER) {
        if (!alarm_armed) {
          float Q = compute_Q_mLph(now_ms);
          if (Q > 0.1f) {
            target_Q_mLph = Q;
            alarm_armed   = 1;
            alarm_level   = ALARM_NONE;
            mute_until_ms = now_ms;          /* no pre-mute carry */
            last_drop_ms  = now_ms;          /* don't NO_DROP-fire immediately */
            Buzzer_PlayFreq(1976U, 80U);     /* B6 ack */
            char tmp[40];
            snprintf(tmp, sizeof(tmp), "BTN MODEhold ARM Q_tgt=%d.%d mL/h",
                     (int)Q, ((int)(Q * 10.0f)) % 10);
            log_msg(tmp);
          } else {
            log_msg("BTN MODEhold ARM rejected (Q=0)");
          }
        } else {
          alarm_armed = 0;
          alarm_level = ALARM_NONE;
          Buzzer_Stop();
          beep_on = 0;
          Buzzer_PlayFreq(1319U, 80U);       /* E6 ack */
          log_msg("BTN MODEhold DISARM");
        }
        view_dirty = 1;
      } else {
        log_msg("BTN MODEhold ignored (in CAL)");
      }
    }

    if (Buttons_MutePressed()) {
      mute_until_ms = now_ms + MUTE_DURATION_MS;
      if (beep_on) { Buzzer_Stop(); beep_on = 0; }
      view_dirty = 1;
      log_msg("BTN MUTE 60s");
    }

    /* Sample both photodiode channels with their own timestamps so the
       interpolation reflects when each one actually converted. */
    uint32_t top_sample_us = TIM2->CNT;
    uint16_t top_raw       = adc_read(ADC_CHANNEL_1);   /* PA1 — TOP */
    uint32_t bot_sample_us = TIM2->CNT;
    uint16_t bot_raw       = adc_read(ADC_CHANNEL_4);   /* PA4 — BOT */

    /* TOP edge detection (hysteretic) with sub-sample timestamp interp */
    if (!top_in && top_raw > top_thresh_high) {
      top_in = 1;
      if (drop_armed && tT_in == 0) {
        tT_in = interp_edge_us(prev_top_raw, prev_top_us,
                               top_raw, top_sample_us, top_thresh_high);
        top_raw_at_in = top_raw;
      }
    } else if (top_in && top_raw < top_thresh_low) {
      top_in = 0;
      if (drop_armed && tT_in != 0 && tT_out == 0) {
        tT_out = interp_edge_us(prev_top_raw, prev_top_us,
                                top_raw, top_sample_us, top_thresh_low);
        top_seq_ok = 1;
      }
    }

    /* BOT edge detection (hysteretic). BOT events only count once the
       TOP entry has been captured — otherwise they're noise. */
    if (!bot_in && bot_raw > bot_thresh_high) {
      bot_in = 1;
      if (drop_armed && top_seq_ok && tB_in == 0) {
        tB_in = interp_edge_us(prev_bot_raw, prev_bot_us,
                               bot_raw, bot_sample_us, bot_thresh_high);
        bot_raw_at_in = bot_raw;
      }
    } else if (bot_in && bot_raw < bot_thresh_low) {
      bot_in = 0;
      if (drop_armed && tB_in != 0 && tB_out == 0) {
        tB_out = interp_edge_us(prev_bot_raw, prev_bot_us,
                                bot_raw, bot_sample_us, bot_thresh_low);

        /* Full drop captured — compute, validate, then route by state. */
        uint32_t dt_us       = tB_in  - tT_in;     /* uint subtraction wraps fine */
        uint32_t tau_us      = tT_out - tT_in;     /* TOP shadow */
        uint32_t pulse_bot_us = tB_out - tB_in;    /* BOT shadow */
        /* 2026-05-13 bench: TOP photodiode produces ~half the pulse width of
           BOT for the same physical drop (TOP/BOT pulse ratio ~0.44-0.48 on
           board 1). Using TOP alone systematically under-reports drop volume.
           Mean of TOP and BOT pulses tracks gravimetric V_true to within the
           per-drop CV across three runs at different flow rates — matches the
           post-processing model in analysis/scripts/load_run.py. */
        uint32_t pulse_mean_us = (tau_us + pulse_bot_us) / 2U;

        /* First-pass guard: pathologically short intervals would blow up
           v = L/Δt. 5 ms = 2 m/s drop over 10 mm — below that something's
           gone wrong (ringing, optical glitch, debounce miss). */
        if (dt_us > 500U && tau_us > 100U) {
          float dt_s     = (float)dt_us        * 1.0e-6f;
          float tau_s    = (float)pulse_mean_us * 1.0e-6f;
          float v_mmps   = (BEAM_PITCH_MM / dt_s) - 0.5f * G_MMPS2 * dt_s;
          /* Chord = ∫v dt = v·τ + ½gτ². v is gravity-corrected at TOP entry;
             using the mean pulse trades a small bias on BOT chord against the
             much larger TOP/BOT optical asymmetry on this board. */
          float chord_mm = v_mmps * tau_s + 0.5f * G_MMPS2 * tau_s * tau_s;
          float d_mm     = chord_mm - BEAM_WIDTH_MM;
          float vol_uL   = (3.14159265f / 6.0f * d_mm * d_mm * d_mm) * V_CAL_K;

          /* Second-pass guard: physical-plausibility floors / ceiling on
             the derived quantities. v could go negative for very slow
             "drops" (long Δt), d negative if chord < W_beam, V huge if
             everything overshoots. Reject and keep prior session state. */
          uint8_t accept = (v_mmps  >= V_MMPS_MIN)
                        && (d_mm    >= D_MM_MIN)
                        && (vol_uL  >  0.0f)
                        && (vol_uL  <= VOL_UL_MAX);

          if (accept) {
            last_drop.dt_us       = dt_us;
            last_drop.tau_us      = tau_us;
            last_drop.v_centi_mps = (int32_t)(v_mmps * 0.1f + 0.5f);
            last_drop.d_tenths    = (int32_t)(d_mm   * 10.0f + 0.5f);
            last_drop.vol_tenths  = (int32_t)(vol_uL * 10.0f + 0.5f);
            last_drop.valid       = 1;
            last_drop_ms          = now_ms;

            {
              char tmp[48];
              snprintf(tmp, sizeof(tmp), "DROP dt=%lu tau=%lu V=%ld.%ld",
                       (unsigned long)(dt_us / 1000U),
                       (unsigned long)(tau_us / 1000U),
                       (long)(last_drop.vol_tenths / 10),
                       (long)(last_drop.vol_tenths % 10));
              log_msg(tmp);

              /* CSV row for offline analysis. Q is the rolling rate at
                 this moment (0 in CAL since compute_Q_mLph returns 0).
                 drop_N is monotonic across accepted drops (this counter is
                 not reset at CAL→METER, so the bench-side parser sees a
                 continuous index even across the state transition). */
              float Q = compute_Q_mLph(now_ms);
              int32_t Q_cmLph = (int32_t)(Q * 100.0f + (Q >= 0 ? 0.5f : -0.5f));
              int state_int = (session_state == STATE_CAL) ? 1 : 2;
              /* pulse_bot_us already in scope from the volume calc above. */
              drops_accepted++;
              log_drop_csv(now_ms, drops_accepted,
                           dt_us,           /* transit_us */
                           tau_us,          /* pulse_top_us */
                           pulse_bot_us,
                           last_drop.v_centi_mps,
                           last_drop.d_tenths,
                           last_drop.vol_tenths,
                           state_int, Q_cmLph,
                           top_raw_at_in, bot_raw_at_in);
            }

            if (session_state == STATE_CAL) {
              if (v_count < CAL_N) {
                v_samples[v_count++] = vol_uL;
              }
              if (v_count >= CAL_N) {
                /* Insertion sort (n = CAL_N), then average middle samples. */
                for (uint8_t i = 1; i < CAL_N; ++i) {
                  float key = v_samples[i];
                  int8_t j  = (int8_t)i - 1;
                  while (j >= 0 && v_samples[j] > key) {
                    v_samples[j + 1] = v_samples[j];
                    j--;
                  }
                  v_samples[j + 1] = key;
                }
                float sum = 0.0f;
                for (uint8_t i = CAL_TRIM_LO; i < (CAL_N - CAL_TRIM_HI); ++i) {
                  sum += v_samples[i];
                }
                v_cal_uL = sum / (float)(CAL_N - CAL_TRIM_LO - CAL_TRIM_HI);
                session_state = STATE_METER;
                {
                  char tmp[40];
                  int32_t vc_t = (int32_t)(v_cal_uL * 10.0f + 0.5f);
                  snprintf(tmp, sizeof(tmp), "CAL DONE Vcal=%ld.%ld uL",
                           (long)(vc_t / 10), (long)(vc_t % 10));
                  log_msg(tmp);
                }
                /* "Cal done" chirp B6 → D7 — blocking; acceptable once /sess. */
                Buzzer_PlayFreq(1976U, 30U);
                HAL_Delay(15U);
                Buzzer_PlayFreq(2349U, 40U);
              }
            } else { /* STATE_METER — push timestamp into ring buffer */
              drop_times_ms[drop_head] = now_ms;
              drop_head = (uint8_t)((drop_head + 1U) % MAX_TRACKED_DROPS);
              if (drop_total < MAX_TRACKED_DROPS) drop_total++;
            }

            view_dirty = 1;
          } else {
            /* Drop rejected by physical-sanity guard — keep prior session
               state, but emit a labelled EVT so the rejection is visible.
               Pen waves typically land in "v_low" because the gravity
               correction makes v_TOP negative for long Δt. */
            const char *r = (v_mmps  < V_MMPS_MIN) ? "v_low"
                          : (d_mm    < D_MM_MIN  ) ? "d_low"
                          : (vol_uL <= 0.0f      ) ? "vol_neg"
                          :                          "vol_hi";
            log_drop_reject(now_ms, r, dt_us, tau_us, v_mmps, d_mm, vol_uL);
          }
        } else {
          /* First-pass guard fired: dt_us or tau_us below the unphysical
             floor. Emit the reject with zeroed physical quantities. */
          log_drop_reject(now_ms, "fast", dt_us, tau_us, 0.0f, 0.0f, 0.0f);
        }

        /* Reset for next drop; require both channels stable-clear before re-arm */
        drop_armed    = 0;
        top_seq_ok    = 0;
        tT_in         = 0;
        tT_out        = 0;
        tB_in         = 0;
        tB_out        = 0;
        top_raw_at_in = 0;
        bot_raw_at_in = 0;
        both_clear_ms = now_ms;
      }
    }

    /* Re-arm after both channels have been quiescently clear (below the
       low-side hysteresis on both) for REARM_CLEAR_MS. */
    if (!drop_armed) {
      uint8_t both_clear = (!top_in && !bot_in
                            && top_raw < top_thresh_low
                            && bot_raw < bot_thresh_low);
      if (!both_clear) {
        both_clear_ms = now_ms;
      } else if ((now_ms - both_clear_ms) >= REARM_CLEAR_MS) {
        drop_armed = 1;
      }
    }

    /* --- Alarm tick: evaluate level, drive non-blocking buzzer pattern.
       Only meaningful when armed and metering. Cleared cleanly when
       disarmed or muted to keep the buzzer line from latching on. */
    if (alarm_armed && session_state == STATE_METER) {
      float Q = compute_Q_mLph(now_ms);
      uint32_t since_drop = now_ms - last_drop_ms;

      alarm_level_t lvl = ALARM_NONE;
      if (target_Q_mLph > 0.1f) {
        float dev = fabsf(Q - target_Q_mLph) / target_Q_mLph;
        if (dev > (ALARM_PCT / 100.0f))     lvl = ALARM_FIRE;
        else if (dev > (WARN_PCT / 100.0f)) lvl = ALARM_WARN;
      }
      if (since_drop > NO_DROP_TIMEOUT_MS) lvl = ALARM_FIRE;

      if (lvl != alarm_level) {
        alarm_level  = lvl;
        view_dirty   = 1;
        next_beep_ms = now_ms;   /* re-cue cadence on level change */
        const char *ln = (lvl == ALARM_FIRE) ? "FIRE"
                       : (lvl == ALARM_WARN) ? "WARN" : "NONE";
        log_msg(ln[0] == 'N' ? "ALARM clear" :
                (ln[0] == 'W' ? "ALARM WARN" : "ALARM FIRE"));
      }

      uint8_t muted = ((int32_t)(mute_until_ms - now_ms) > 0);
      if (alarm_level != ALARM_NONE && !muted) {
        if ((int32_t)(now_ms - next_beep_ms) >= 0) {
          if (!beep_on) {
            uint16_t f      = (alarm_level == ALARM_FIRE) ? ALARM_BEEP_HZ : WARN_BEEP_HZ;
            uint16_t on_ms  = (alarm_level == ALARM_FIRE) ? ALARM_BEEP_ON_MS : WARN_BEEP_ON_MS;
            Buzzer_StartTone(f);
            beep_on = 1;
            next_beep_ms = now_ms + on_ms;
          } else {
            Buzzer_Stop();
            beep_on = 0;
            uint16_t off_ms = (alarm_level == ALARM_FIRE) ? ALARM_BEEP_OFF_MS : WARN_BEEP_OFF_MS;
            next_beep_ms = now_ms + off_ms;
          }
        }
      } else if (beep_on) {
        Buzzer_Stop();
        beep_on = 0;
      }
    } else if (beep_on) {
      Buzzer_Stop();
      beep_on = 0;
    }

    /* Periodic redraw for views whose content changes without a drop:
       RAW follows live ADC values; FLOW must decay Q as drops age out
       of the window and show alarm/arm state changes. DROP only changes
       on a new drop. 5 Hz is fine — full 4-line LCD refresh ≈ 2 ms SPI. */
    if ((now_ms - last_periodic_ms) >= 200U) {
      if (view == VIEW_RAW || view == VIEW_FLOW) view_dirty = 1;
      last_periodic_ms = now_ms;
    }

    if (view_dirty) {
      switch (view) {
        case VIEW_DROP: render_drop(); break;
        case VIEW_FLOW: render_flow(now_ms); break;
        case VIEW_RAW:  render_raw(top_raw, bot_raw,
                                   top_thresh_high, bot_thresh_high,
                                   top_in, bot_in, drop_armed, top_seq_ok); break;
        case VIEW_COUNT: break;  /* unreachable — for switch completeness */
      }
      view_dirty = 0;
    }

    /* Snapshot this iteration's samples as "previous" for next-cycle interp. */
    prev_top_raw = top_raw;
    prev_top_us  = top_sample_us;
    prev_bot_raw = bot_raw;
    prev_bot_us  = bot_sample_us;
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

  /** Configure LSE Drive Capability
  */
  HAL_PWR_EnableBkUpAccess();
  __HAL_RCC_LSEDRIVE_CONFIG(RCC_LSEDRIVE_LOW);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI|RCC_OSCILLATORTYPE_LSE;
  RCC_OscInitStruct.LSEState = RCC_LSE_ON;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSIDiv = RCC_HSI_DIV1;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = RCC_PLLM_DIV1;
  RCC_OscInitStruct.PLL.PLLN = 8;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV4;
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
  * @brief COMP1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_COMP1_Init(void)
{

  /* USER CODE BEGIN COMP1_Init 0 */

  /* USER CODE END COMP1_Init 0 */

  /* USER CODE BEGIN COMP1_Init 1 */

  /* USER CODE END COMP1_Init 1 */
  hcomp1.Instance = COMP1;
  hcomp1.Init.InputPlus = COMP_INPUT_PLUS_IO3;
  hcomp1.Init.InputMinus = COMP_INPUT_MINUS_1_2VREFINT;
  hcomp1.Init.OutputPol = COMP_OUTPUTPOL_NONINVERTED;
  hcomp1.Init.WindowOutput = COMP_WINDOWOUTPUT_EACH_COMP;
  hcomp1.Init.Hysteresis = COMP_HYSTERESIS_LOW;
  hcomp1.Init.BlankingSrce = COMP_BLANKINGSRC_NONE;
  hcomp1.Init.Mode = COMP_POWERMODE_HIGHSPEED;
  hcomp1.Init.WindowMode = COMP_WINDOWMODE_DISABLE;
  hcomp1.Init.TriggerMode = COMP_TRIGGERMODE_NONE;
  if (HAL_COMP_Init(&hcomp1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN COMP1_Init 2 */

  /* USER CODE END COMP1_Init 2 */

}

/**
  * @brief LPTIM1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_LPTIM1_Init(void)
{

  /* USER CODE BEGIN LPTIM1_Init 0 */

  /* USER CODE END LPTIM1_Init 0 */

  /* USER CODE BEGIN LPTIM1_Init 1 */

  /* USER CODE END LPTIM1_Init 1 */
  hlptim1.Instance = LPTIM1;
  hlptim1.Init.Clock.Source = LPTIM_CLOCKSOURCE_APBCLOCK_LPOSC;
  hlptim1.Init.Clock.Prescaler = LPTIM_PRESCALER_DIV1;
  hlptim1.Init.UltraLowPowerClock.Polarity = LPTIM_CLOCKPOLARITY_RISING;
  hlptim1.Init.UltraLowPowerClock.SampleTime = LPTIM_CLOCKSAMPLETIME_DIRECTTRANSITION;
  hlptim1.Init.Trigger.Source = LPTIM_TRIGSOURCE_SOFTWARE;
  hlptim1.Init.OutputPolarity = LPTIM_OUTPUTPOLARITY_HIGH;
  hlptim1.Init.UpdateMode = LPTIM_UPDATE_IMMEDIATE;
  hlptim1.Init.CounterSource = LPTIM_COUNTERSOURCE_EXTERNAL;
  hlptim1.Init.Input1Source = LPTIM_INPUT1SOURCE_COMP1;
  hlptim1.Init.Input2Source = LPTIM_INPUT2SOURCE_GPIO;
  if (HAL_LPTIM_Init(&hlptim1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN LPTIM1_Init 2 */

  /* USER CODE END LPTIM1_Init 2 */

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
  htim1.Init.Period = 249;
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
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  huart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart1.Init.ClockPrescaler = UART_PRESCALER_DIV1;
  huart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetTxFifoThreshold(&huart1, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetRxFifoThreshold(&huart1, UART_RXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_DisableFifoMode(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

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

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(BST_MODE_GPIO_Port, BST_MODE_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, LCD_CS_Pin|LCD_RST_Pin|LED_CTRL_BOT_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin : BST_MODE_Pin */
  GPIO_InitStruct.Pin = BST_MODE_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(BST_MODE_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : LCD_CS_Pin LCD_RST_Pin LED_CTRL_BOT_Pin */
  GPIO_InitStruct.Pin = LCD_CS_Pin|LCD_RST_Pin|LED_CTRL_BOT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pins : BTN_MUTE_Pin BTN_MODE_Pin */
  GPIO_InitStruct.Pin = BTN_MUTE_Pin|BTN_MODE_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pin : BTN_RES_Pin */
  GPIO_InitStruct.Pin = BTN_RES_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(BTN_RES_GPIO_Port, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */
  /* Override BTN_RES pull config: CubeMX sets NOPULL, which lets the pin
     float when the button isn't populated. Force pull-up so unused/open
     reads as SET. Update the .ioc to match when regenerating.             */
  GPIO_InitStruct.Pin  = BTN_RES_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(BTN_RES_GPIO_Port, &GPIO_InitStruct);
  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
static uint16_t adc_read(uint32_t channel)
{
  ADC_ChannelConfTypeDef sConfig = {0};
  sConfig.Channel = channel;
  sConfig.Rank = ADC_REGULAR_RANK_1;
  sConfig.SamplingTime = ADC_SAMPLINGTIME_COMMON_1;
  HAL_ADC_ConfigChannel(&hadc1, &sConfig);
  HAL_ADC_Start(&hadc1);
  HAL_ADC_PollForConversion(&hadc1, 10);
  uint16_t v = (uint16_t)HAL_ADC_GetValue(&hadc1);
  HAL_ADC_Stop(&hadc1);
  return v;
}

static void lcd_put_at(uint8_t line, uint8_t col, char c)
{
  static const uint8_t addr[4] = {0x00, 0x20, 0x40, 0x60};
  if (line >= 4 || col >= 16) return;
  LCD_WriteCmd(0x80 | (addr[line] + col));
  LCD_WriteData((uint8_t)c);
}

/* Sub-sample timestamp interpolation. Given two ADC samples that bracket
   a threshold crossing (v_prev below, v_now above for a rising edge — or
   the other way for falling), return the time at which the signal would
   have crossed `v_threshold` if it had been linear between the samples.
   Falls back to t_now_us when the samples are non-monotone (shouldn't
   happen given the hysteretic state machine but cheap to handle). */
static uint32_t interp_edge_us(uint16_t v_prev, uint32_t t_prev_us,
                               uint16_t v_now,  uint32_t t_now_us,
                               uint16_t v_threshold)
{
  uint32_t delta_us = t_now_us - t_prev_us;       /* unsigned wrap-safe */
  int32_t  span     = (int32_t)v_now - (int32_t)v_prev;
  int32_t  gap      = (int32_t)v_threshold - (int32_t)v_prev;

  if (span == 0) return t_now_us;                  /* flat — give up   */
  if ((span > 0 && gap <= 0) ||                    /* threshold not in */
      (span < 0 && gap >= 0)) return t_now_us;     /* the [prev, now]  */
                                                   /* interval         */
  /* abs() of span/gap, fixed-point fraction × delta_us. The cast to
     int64 keeps the multiplication from overflowing at large delta_us;
     adding den/2 before division rounds to nearest µs. */
  int64_t num = (int64_t)((gap > 0) ? gap : -gap) * (int64_t)delta_us;
  int64_t den = (int64_t)((span > 0) ? span : -span);
  uint32_t offset = (uint32_t)((num + den / 2) / den);
  return t_prev_us + offset;
}

/* Rolling flow rate Q in mL/h, computed by counting drop timestamps in
   the ring buffer that fall within WINDOW_MS of now_ms. Returns 0 when
   the session hasn't calibrated yet or no drops have landed. */
static float compute_Q_mLph(uint32_t now_ms)
{
  if (session_state != STATE_METER) return 0.0f;
  uint8_t n    = 0;
  uint8_t scan = (drop_total < MAX_TRACKED_DROPS) ? drop_total : MAX_TRACKED_DROPS;
  for (uint8_t i = 0; i < scan; ++i) {
    uint8_t idx = (uint8_t)((drop_head + MAX_TRACKED_DROPS - 1U - i) % MAX_TRACKED_DROPS);
    if ((now_ms - drop_times_ms[idx]) <= WINDOW_MS) {
      n++;
    } else {
      break;       /* older entries are older — early-exit */
    }
  }
  float window_s = (float)WINDOW_MS / 1000.0f;
  return ((float)n * v_cal_uL / window_s) * 3.6f;   /* µL/s → mL/h */
}

/* Write s to `line`, padding right with spaces to exactly 16 chars.
   LCD_Print walks the string until NUL — without padding, leftover
   chars from a previous view persist. */
static void lcd_line_padded(uint8_t line, const char *s)
{
  char buf[17];
  uint8_t i = 0;
  while (i < 16 && s[i]) { buf[i] = s[i]; i++; }
  while (i < 16) { buf[i++] = ' '; }
  buf[16] = '\0';
  LCD_Print(line, buf);
}

/* VIEW_DROP — last drop's raw math. The user can verify every step of
   the chain: dt → vT → τT → V. Stale until the next drop arrives.       */
static void render_drop(void)
{
  char tmp[28];
  if (!last_drop.valid) {
    lcd_line_padded(0, "dt:   --- ms");
    lcd_line_padded(1, "vT:  ---- m/s");
    lcd_line_padded(2, "tT:   --- ms");
    lcd_line_padded(3, "V:   ---- uL");
    return;
  }
  uint32_t dt_tenths  = (last_drop.dt_us  + 50U) / 100U;
  uint32_t tau_tenths = (last_drop.tau_us + 50U) / 100U;
  int32_t  v_c        = last_drop.v_centi_mps;
  int32_t  vol_t      = last_drop.vol_tenths;

  snprintf(tmp, sizeof(tmp), "dt:%4lu.%lu ms",
           (unsigned long)(dt_tenths / 10U),
           (unsigned long)(dt_tenths % 10U));
  lcd_line_padded(0, tmp);

  snprintf(tmp, sizeof(tmp), "vT:%3ld.%02ld m/s",
           (long)(v_c / 100),
           (long)((v_c < 0 ? -v_c : v_c) % 100));
  lcd_line_padded(1, tmp);

  snprintf(tmp, sizeof(tmp), "tT:%4lu.%lu ms",
           (unsigned long)(tau_tenths / 10U),
           (unsigned long)(tau_tenths % 10U));
  lcd_line_padded(2, tmp);

  snprintf(tmp, sizeof(tmp), "V:%4ld.%ld uL",
           (long)(vol_t / 10),
           (long)((vol_t < 0 ? -vol_t : vol_t) % 10));
  lcd_line_padded(3, tmp);
}

/* VIEW_FLOW — clinical / calibration view. During CAL: progress + last V
   + running min/max of accepted samples. After CAL: rolling Q, V_cal,
   drops in window, latest V. */
static void render_flow(uint32_t now_ms)
{
  char tmp[28];

  if (session_state == STATE_CAL) {
    snprintf(tmp, sizeof(tmp), "Calibrating %u/%u",
             (unsigned)v_count, (unsigned)CAL_N);
    lcd_line_padded(0, tmp);

    if (last_drop.valid) {
      int32_t v = last_drop.vol_tenths;
      snprintf(tmp, sizeof(tmp), "Last V:%3ld.%ld uL",
               (long)(v / 10),
               (long)((v < 0 ? -v : v) % 10));
      lcd_line_padded(1, tmp);
    } else {
      lcd_line_padded(1, "Last V: ---- uL");
    }

    if (v_count >= 2) {
      float vmin = v_samples[0], vmax = v_samples[0];
      for (uint8_t i = 1; i < v_count; ++i) {
        if (v_samples[i] < vmin) vmin = v_samples[i];
        if (v_samples[i] > vmax) vmax = v_samples[i];
      }
      int32_t lo = (int32_t)(vmin * 10.0f + 0.5f);
      int32_t hi = (int32_t)(vmax * 10.0f + 0.5f);
      snprintf(tmp, sizeof(tmp), "lo%3ld.%ld hi%3ld.%ld",
               (long)(lo / 10), (long)(lo % 10),
               (long)(hi / 10), (long)(hi % 10));
      lcd_line_padded(2, tmp);
    } else {
      lcd_line_padded(2, "lo --- hi ---");
    }

    lcd_line_padded(3, "Q: pending cal");
    return;
  }

  /* STATE_METER: count drops within the last WINDOW_MS, compute Q. */
  uint8_t n = 0;
  uint8_t scan = (drop_total < MAX_TRACKED_DROPS) ? drop_total : MAX_TRACKED_DROPS;
  for (uint8_t i = 0; i < scan; ++i) {
    uint8_t idx = (uint8_t)((drop_head + MAX_TRACKED_DROPS - 1U - i) % MAX_TRACKED_DROPS);
    uint32_t age = now_ms - drop_times_ms[idx];
    if (age <= WINDOW_MS) {
      n++;
    } else {
      break;  /* older entries are older — early-exit the scan */
    }
  }

  float window_s = (float)WINDOW_MS / 1000.0f;
  float Q_uLps   = (float)n * v_cal_uL / window_s;     /* µL/s          */
  float Q_mLph   = Q_uLps * 3.6f;                       /* mL/h          */
  int32_t Q_t    = (int32_t)(Q_mLph  * 10.0f + 0.5f);
  int32_t vc_t   = (int32_t)(v_cal_uL * 10.0f + 0.5f);

  /* Compose Q line with a small status marker: !! for ALARM, ! for WARN,
     M while muted, blank when armed-clean / not-armed. */
  uint8_t muted = ((int32_t)(mute_until_ms - now_ms) > 0);
  const char *mark = "";
  if (alarm_armed) {
    if      (muted)                          mark = " M";
    else if (alarm_level == ALARM_FIRE)      mark = "!!";
    else if (alarm_level == ALARM_WARN)      mark = " !";
  }
  snprintf(tmp, sizeof(tmp), "Q:%4ld.%ld mL/h%s",
           (long)(Q_t / 10), (long)(Q_t % 10), mark);
  lcd_line_padded(0, tmp);

  snprintf(tmp, sizeof(tmp), "Vcal:%3ld.%ld uL",
           (long)(vc_t / 10), (long)(vc_t % 10));
  lcd_line_padded(1, tmp);

  snprintf(tmp, sizeof(tmp), "Drops/%lus: %2u",
           (unsigned long)(WINDOW_MS / 1000U), (unsigned)n);
  lcd_line_padded(2, tmp);

  /* Line 3: arm/alarm status if armed, else last-drop volume.            */
  if (!alarm_armed) {
    if (last_drop.valid) {
      int32_t v = last_drop.vol_tenths;
      snprintf(tmp, sizeof(tmp), "Last V:%3ld.%ld uL",
               (long)(v / 10), (long)((v < 0 ? -v : v) % 10));
      lcd_line_padded(3, tmp);
    } else {
      lcd_line_padded(3, "Last V: ----");
    }
  } else if (muted) {
    uint32_t s_left = (mute_until_ms - now_ms) / 1000U;
    snprintf(tmp, sizeof(tmp), "MUTED %lus", (unsigned long)s_left);
    lcd_line_padded(3, tmp);
  } else if (alarm_level != ALARM_NONE) {
    uint32_t since_drop = now_ms - last_drop_ms;
    if (since_drop > NO_DROP_TIMEOUT_MS) {
      lcd_line_padded(3, (alarm_level == ALARM_FIRE) ? "ALARM no drops" : "WARN  no drops");
    } else if (target_Q_mLph > 0.1f) {
      float dev_pct = (Q_mLph - target_Q_mLph) / target_Q_mLph * 100.0f;
      int32_t dev   = (int32_t)(dev_pct + (dev_pct >= 0 ? 0.5f : -0.5f));
      if (dev > 99) dev = 99; else if (dev < -99) dev = -99;
      char sign = (dev >= 0) ? '+' : '-';
      int32_t mag = (dev >= 0) ? dev : -dev;
      const char *lbl = (alarm_level == ALARM_FIRE) ? "ALARM" : "WARN ";
      snprintf(tmp, sizeof(tmp), "%s dev:%c%ld%%",
               lbl, sign, (long)mag);
      lcd_line_padded(3, tmp);
    } else {
      lcd_line_padded(3, "ALARM (no Tgt)");
    }
  } else {
    int32_t tgt = (int32_t)(target_Q_mLph + 0.5f);
    snprintf(tmp, sizeof(tmp), "ARM @%3ld mL/h", (long)tgt);
    lcd_line_padded(3, tmp);
  }
}

/* VIEW_RAW — live ADC values, calibrated thresholds, and the edge-state
   flags. Use this view to diagnose why a drop isn't registering: is the
   ADC moving? Does it cross the threshold? Did the edge-detector see it?
   Is the arm/seq state stuck? */
static void render_raw(uint16_t top_raw, uint16_t bot_raw,
                       uint16_t top_hi, uint16_t bot_hi,
                       uint8_t top_in, uint8_t bot_in,
                       uint8_t armed, uint8_t seq_ok)
{
  char tmp[28];
  snprintf(tmp, sizeof(tmp), "T:%4u hi:%4u",
           (unsigned)top_raw, (unsigned)top_hi);
  lcd_line_padded(0, tmp);

  snprintf(tmp, sizeof(tmp), "B:%4u hi:%4u",
           (unsigned)bot_raw, (unsigned)bot_hi);
  lcd_line_padded(1, tmp);

  snprintf(tmp, sizeof(tmp), "in T:%c B:%c arm:%c",
           top_in ? '1' : '0',
           bot_in ? '1' : '0',
           armed  ? '1' : '0');
  lcd_line_padded(2, tmp);

  if (session_state == STATE_CAL) {
    snprintf(tmp, sizeof(tmp), "seq:%c CAL %u/%u",
             seq_ok ? '1' : '0',
             (unsigned)v_count, (unsigned)CAL_N);
  } else {
    /* "al:" sub-field tracks alarm state so the user can verify the
       button bindings and the alarm logic without leaving RAW view:
         --  not armed
         OK  armed, within ±WARN_PCT of target
         WN  warning  (between ±WARN_PCT and ±ALARM_PCT)
         AL  alarming (> ±ALARM_PCT or NO_DROP_TIMEOUT)
         MU  alarm muted */
    const char *al;
    if (!alarm_armed)                    al = "--";
    else {
      uint32_t now_ms_ = HAL_GetTick();
      uint8_t muted = ((int32_t)(mute_until_ms - now_ms_) > 0);
      if      (muted)                    al = "MU";
      else if (alarm_level == ALARM_FIRE) al = "AL";
      else if (alarm_level == ALARM_WARN) al = "WN";
      else                                al = "OK";
    }
    snprintf(tmp, sizeof(tmp), "seq:%c d:%2u al:%s",
             seq_ok ? '1' : '0',
             (unsigned)((drop_total > 99U) ? 99U : drop_total),
             al);
  }
  lcd_line_padded(3, tmp);
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
