# KNBS Census Data Extraction Template

## Priority Extraction Plan

### 🔥 **CRITICAL - THIS WEEK**

#### Volume I: Population by County and Sub-County
**Target**: Replace inaccurate Atlas population data

**Key Tables to Extract:**
1. **Table 2.2: Distribution of Population by Sex and County** ✅ (You already provided this)
2. **Sub-county Population Tables** (Look for tables with format like this):

```csv
# Template: knbs_subcounty_population_2019.csv
county,subcounty,male,female,intersex,total_population,rural_population,urban_population
Baringo,Baringo Central,59805,59805,7,119610,119610,0
Baringo,Baringo North,69067,69067,0,138134,138134,0
Baringo,Baringo South,58736,58735,0,117471,117471,0
...
```

#### Volume IV: Socio-Economic Characteristics  
**Target**: Education and poverty data for adaptive capacity

**Key Tables to Extract:**
1. **Education Levels by Sub-county** (Look for tables showing):
   - No education percentage
   - Primary education completion
   - Secondary education completion  
   - Tertiary education percentage

```csv
# Template: knbs_education_2019.csv
county,subcounty,no_education_pct,primary_completed_pct,secondary_completed_pct,tertiary_pct,total_population
Baringo,Baringo Central,15.2,45.8,28.5,10.5,119610
...
```

2. **Employment and Economic Indicators** (Look for tables showing):
   - Employment status
   - Main occupation (especially agriculture)
   - Economic activity participation

```csv
# Template: knbs_employment_2019.csv
county,subcounty,employed_pct,unemployed_pct,agriculture_employment_pct,total_working_age
Baringo,Baringo Central,65.2,8.5,72.1,85000
...
```

## 📋 **Extraction Workflow**

### Step 1: Locate Tables (Today)
- [ ] Access Volume I PDF/physical copy
- [ ] Find sub-county population tables (likely Section 2 or 3)
- [ ] Access Volume IV PDF/physical copy  
- [ ] Find education tables (likely Section 4 or 5)
- [ ] Find employment tables (likely Section 6 or 7)

### Step 2: Extract Data (This Week)
- [ ] Create CSV files using templates above
- [ ] Manually transcribe key tables
- [ ] Focus on all 290 sub-counties
- [ ] Double-check county totals against Table 2.2

### Step 3: Validate (This Week)
- [ ] Sum sub-county totals to verify county totals
- [ ] Compare with our existing Atlas data
- [ ] Check for missing sub-counties
- [ ] Validate administrative unit names

### Step 4: Integration (Next Week)
- [ ] Replace Atlas population data with KNBS data
- [ ] Integrate education data with vulnerability indicators
- [ ] Update adaptive capacity calculations
- [ ] Retrain resilience model

## 🎯 **Expected Data Structure**

### Final Integrated Dataset for Step 4:
```csv
# Master socioeconomic dataset
county,subcounty,total_population,male,female,rural_population,urban_population,
no_education_pct,primary_completed_pct,secondary_completed_pct,tertiary_pct,
employed_pct,agriculture_employment_pct,vulnerability_score,adaptive_capacity_score

Baringo,Baringo Central,119610,59805,59805,119610,0,
15.2,45.8,28.5,10.5,
65.2,72.1,2.5,7.2
...
```

## 📊 **Quality Checks**

### Population Data Validation:
- [ ] County totals match Table 2.2 exactly
- [ ] All 290 sub-counties included
- [ ] Male + Female + Intersex = Total Population
- [ ] Rural + Urban = Total Population

### Education Data Validation:
- [ ] Education percentages sum to 100% (approximately)
- [ ] Data available for all 290 sub-counties
- [ ] Reasonable ranges (no education: 5-40%, tertiary: 2-25%)

### Administrative Validation:
- [ ] Sub-county names match our boundary files
- [ ] County names consistent across datasets
- [ ] No duplicate entries

## 🚀 **Phase I Integration Impact**

### Before Census Extraction:
- Step 4: 🟡 **Partial** (Atlas data with 146% discrepancy)
- Overall: **3.5/4 steps ready**

### After Census Extraction:
- Step 4: ✅ **Complete** (Official KNBS data)
- Overall: **4/4 steps ready with high confidence**

### Resilience Model Enhancement:
1. **Population Weighting**: Accurate sub-county populations for resilience score weighting
2. **Adaptive Capacity**: Education levels directly improve vulnerability modeling
3. **Rural Focus**: Rural population percentages for agricultural targeting
4. **Economic Context**: Employment data for economic resilience assessment

## 📅 **Timeline**

| Week | Action | Deliverable |
|------|--------|------------|
| This Week | Extract Volume I & IV tables | CSV files with census data |
| Next Week | Integrate with existing data | Updated Step 4 implementation |
| Week 3 | Model retraining | Enhanced resilience engine |
| Week 4 | Validation & testing | Production-ready model |

## 💡 **Pro Tips for Extraction**

1. **Start with Volume I**: Population data is most critical
2. **Use county totals as validation**: Sum sub-counties to verify accuracy
3. **Focus on rural areas**: Most relevant for agricultural resilience
4. **Prioritize education data**: Strongest predictor of adaptive capacity
5. **Cross-reference boundary names**: Ensure consistency with our spatial data

This census data extraction will transform Agri-Adapt AI from a "working prototype" to an "authoritative tool" with official government data backing every calculation.

**Ready to begin extraction?** Start with Volume I, Table 2.2 validation, then move to sub-county tables!