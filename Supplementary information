## Allocation Equations

This section describes the allocation rules for electricity consumption and distribution, considering hourly, yearly, monthly, and daily caps.

---

### 1. Hourly Allocation  
The **hourly allocation** determines how much electricity is taken from the **grid** and how much is unclaimed from PV generation at an hourly level.

$$ H_{\text{grid}} = \max\left( 0, E_{\text{elec, total}} - E_{\text{elec, direct PV}} \right) $$  
$$ H_{\text{not claimed}} = E_{\text{PV, total}} - E_{\text{elec, direct PV}} $$  

where:  

- E_elec, total = electrolyzer capacity × capacity factor × 8760 (total yearly electricity required by the electrolyzer)  
- E_elec, direct PV = electricity directly consumed by the electrolyzer from PV (instantaneous consumption)  
- E_PV, total = total yearly PV electricity production
- H_grid is the electricity **taken from the grid** under an hourly time allocation
- H_not claimed is the **surplus PV electricity** not used by the electrolyzer (can be stored or sold). 

If the electrolyzer needs more electricity than what PV directly provides, the grid supplies the difference. Any excess PV electricity that is not used directly is **not claimed**.

---

### 2. Yearly Allocation  
The **yearly allocation** considers how much electricity can be claimed as PV-sourced over an entire year.

$$ Y_{\text{elec from PV}} = \min(E_{\text{elec, total}}, E_{\text{PV, total}}) $$  
$$ Y_{\text{not claimed}} = \max(0, E_{\text{PV, total}} - E_{\text{elec, total}}) $$  
$$ Y_{\text{credit}} = Y_{\text{elec from PV}} - E_{\text{elec, direct PV}} $$  
$$ Y_{\text{grid}} = E_{\text{elec, total}} - Y_{\text{elec from PV}} $$  

where: 
- Y_elec from PV is the **total electricity** that can be claimed as PV-sourced.  
- Y_not claimed is the **surplus PV electricity** not used by the electrolyzer (can be stored or sold).  
- Y_credit is the electricity that was **sent to the grid but later reclaimed** as PV electricity.  
- Y_grid is the electricity **taken from the grid** if PV electricity is insufficient.  

If the PV system produces **more** than what the electrolyzer consumes, the excess is **not claimed**. If PV produces **less**, the grid supplies the difference.

---

### 3. Monthly Allocation  
The **monthly allocation** applies a cap on how much PV electricity can be claimed each month, ensuring that grid and PV allocations align with monthly energy availability.

$$ M_{\text{elec from PV}} = \sum_{m=1}^{12} \min\left(E_{\text{PV, month}}[m], \text{monthly cap} \right) $$  
$$ M_{\text{not claimed}} = E_{\text{PV, total}} - M_{\text{elec from PV}} $$  
$$ M_{\text{credit}} = M_{\text{elec from PV}} - E_{\text{elec, direct PV}} $$  
$$ M_{\text{grid}} = E_{\text{elec, total}} - M_{\text{elec from PV}} $$  

where:  
- E_PV, month [m] = electricity produced by PV during month **m**.  
- **monthly cap** = number of days in the month × 24 × electrolyzer capacity.
- M_elec from PV is the PV electricity that the electrolyzer consumes daily.  
- M_not claimed is the **excess PV electricity** not consumed.  
- M_credit represents electricity that was sent to the grid but later claimed as PV-sourced.  
- M_grid is the electricity taken from the grid if PV is insufficient.  

This allocation ensures that monthly PV electricity consumption does not exceed the electrolyzer's capacity.

---

### 4. Daily Allocation  
The **daily allocation** applies a cap at the **daily level** to determine how much PV electricity can be claimed as used.

$$ D_{\text{elec from PV}} = \sum_{d=1}^{365} \min\left(E_{\text{PV, day}}[d], \text{daily cap} \right) $$  
$$ D_{\text{not claimed}} = E_{\text{PV, total}} - D_{\text{elec from PV}} $$  
$$ D_{\text{credit}} = D_{\text{elec from PV}} - E_{\text{elec, direct PV}} $$  
$$ D_{\text{grid}} = E_{\text{elec, total}} - D_{\text{elec from PV}} $$  

where: 
- E_PV, day [d] = electricity produced by PV during day **d**. 
- **daily cap** = 24 x electrolyzer capacity
- D_elec from PV is the PV electricity that the electrolyzer consumes daily.
- D_not claimed is the **excess PV electricity** not consumed.  
- D_credit represents electricity that was sent to the grid but later claimed as PV-sourced.  
- D_grid is the electricity taken from the grid if PV is insufficient.  

This allocation ensures that the electrolyzer does not **over-claim** PV electricity beyond what is feasible on a **daily basis**.

---

## Summary
The allocation methods define how much electricity is sourced from **PV** and how much comes from the **grid**, depending on the **time resolution**:
- **Hourly:** Direct PV consumption and grid use in real-time.
- **Yearly:** Total PV electricity that can be claimed over a year.
- **Monthly:** Ensures PV electricity claims do not exceed monthly production.
- **Daily:** Caps electricity consumption to daily PV availability.

---
