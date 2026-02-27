#include "alarm.h"
#include "buzzer.h"
#include "main.h"

extern volatile uint32_t last_drop_ms;
extern volatile float    flow_mlh;
extern volatile uint16_t target_rate_mlh;

static enum alarm_id_e active_alarm = ALARM_NONE;
static uint32_t         flow_dev_start_ms = 0;
static uint32_t         last_beep_ms = 0;
static bool             muted = false;

static void alarm_trigger(enum alarm_id_e id)
{
    active_alarm = id;
    muted = false;
    ui_alarm_start(id);
}

void alarm_task(void)
{
    uint32_t now = HAL_GetTick();

    /* handle active alarm */
    if (active_alarm != ALARM_NONE) {
        if (!muted && (now - last_beep_ms >= 500U)) {
            last_beep_ms = now;
            Buzzer_PlayFreq(4000, 50);
        }

        if (active_alarm == ALARM_STOP) {
            if ((now - last_drop_ms) < 15000U) {
                active_alarm = ALARM_NONE;
                ui_alarm_clear();
            }
        } else if (active_alarm == ALARM_FLOW) {
            float diff = flow_mlh > target_rate_mlh ?
                          (flow_mlh - target_rate_mlh) :
                          (target_rate_mlh - flow_mlh);
            if (diff <= ((float)target_rate_mlh * 0.1f)) {
                active_alarm = ALARM_NONE;
                ui_alarm_clear();
                flow_dev_start_ms = 0;
            }
        }
        return;
    }

    /* stop alarm: no drop for 15 s */
    if ((now - last_drop_ms) >= 15000U) {
        alarm_trigger(ALARM_STOP);
        return;
    }

    /* flow alarm: deviation >10% for 10 s */
    if (target_rate_mlh > 0U) {
        float diff = flow_mlh > target_rate_mlh ?
                      (flow_mlh - target_rate_mlh) :
                      (target_rate_mlh - flow_mlh);
        if (diff > ((float)target_rate_mlh * 0.1f)) {
            if (flow_dev_start_ms == 0U) {
                flow_dev_start_ms = now;
            } else if ((now - flow_dev_start_ms) >= 10000U) {
                alarm_trigger(ALARM_FLOW);
            }
        } else {
            flow_dev_start_ms = 0U;
        }
    } else {
        flow_dev_start_ms = 0U;
    }
}

void alarm_mute(void)
{
    muted = true;
    buzzer_mute();
}
