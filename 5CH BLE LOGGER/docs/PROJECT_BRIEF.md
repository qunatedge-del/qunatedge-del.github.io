# Project: 5-Channel K-Type Thermocouple BLE Data Logger (High-Precision CJC)

> 使用者原始需求（逐字保留，英文）。Please act as a Senior Hardware Engineer and PCB Layout Expert.
> I am designing a low-power data logger. Generate a detailed schematic netlist, a system block diagram,
> and critical PCB layout instructions based on the following system architecture.

## 1. System Overview
- Power source: 4 x AA batteries (approx. 6.0 V fresh, drops to ~3.6 V when depleted).
- Main MCU: WCH CH583 (RISC-V, BLE 5.3, dual SPI).
- Analog front-end (AFE): 5 x SD6500 (high-precision Sigma-Delta ADC with internal PGA, 2-wire interface).
- Sensors: 5 x K-type thermocouples + 1 x NTC thermistor (shared cold-junction compensation).
- Peripherals: SPI LCD screen, SPI Flash (data logging).
- System voltage: entire digital system on a regulated 3.3 V rail.

## 2. Power supply circuit (CE8503AM buck converter) — exact circuit requested
- Input: SYS_PWR (4xAA battery positive). IC: U3 = CE8503AM (SOT-23-5, "M" pinout).
- Pin 4 (VIN): SYS_PWR, decoupled with C22 (10 uF) and C27 (1 uF) to GND.
- Pin 1 (EN): net PB1 (MCU control or pull-up to VIN).
- Pin 2 (GND): system ground.
- Pin 3 (LX): inductor L3 (2.2 uH); other side of L3 is VCC_3V3.
- Pin 5 (FB): midpoint of divider from VCC_3V3 (R29 = 180 k top, R30 = 39 k bottom to GND);
  feed-forward cap C38 (22 pF) in parallel with R29.
- Output VCC_3V3: C23 (10 uF), C16 (0.1 uF), C39 (100 uF / 10 V tantalum).
- The user's schematic of this section: `../reference/power_section_user_schematic.png`

## 3. Sensor array (5 x SD6500 + shared NTC)
- Power: pin 7 (VDD) of all 5 chips to VCC_3V3 (10 uF and 0.1 uF decoupling). Pin 8 DVSS. Pin 5 AVSS.
- Internal LDO: pin 6 (AVDDR) of each chip needs 0.1 uF to AVSS.
- K-type inputs (all 5 chips): pin 1 (AI0) and pin 2 (AI1) of each SD6500 connect to a K-type thermocouple
  connector through a differential RC low-pass filter.
- NTC CJC (SD6500 #1 ONLY): NTC + precision reference resistor (e.g. 10 k 0.1 %) as a divider powered from
  AVDDR (pin 6) of SD6500 #1; the midpoint connects to pin 3 (AI6) and pin 4 (AI7) of SD6500 #1 for
  ratiometric measurement.   <-- see HANDOFF "Issue 1": as written this does not work.
- Digital: SCK (pin 9) of all 5 chips tied together to ONE CH583 GPIO.
  DATA (pin 10): 5 independent lines to 5 separate CH583 GPIOs (parallel sampling).

## 4. MCU (WCH CH583)
- Powered by VCC_3V3. SPI0 -> external SPI Flash. SPI1 -> LCD display.
- ADC control: 1 GPIO for shared SCK, 5 GPIOs for the SD6500 DATA lines.

## Deliverables requested
1. Netlist & pin mapping: text pin connection table for MCU, ADCs, power, sensors.
2. Schematic block diagram: Mermaid.js diagram of power flow and data connections.
3. Critical PCB layout instructions: the "Isothermal Block" (等溫區): how the 5 K-type terminals and the single
   NTC are placed physically, and how GND copper pours are routed so all 5 channels share the same thermal
   reference without gradients.
4. (Added later) Draw the schematic in KiCad through the KiCad MCP on the user's own computer.
