# Facebook Rate Limit Optimization Guide

Based on your Meta dashboard statistics showing 289 API calls with most being redundant page info requests, here's a comprehensive optimization strategy.

## 📊 Current Usage Analysis

**Your API Call Breakdown:**
- `gr:get:PageName` - **156 calls** (54% of usage) - **MOST WASTEFUL**
- `gr:get:Page` - **80 calls** (28% of usage) - **REDUNDANT**
- `gr:get:User` - **28 calls** (10% of usage)
- `gr:get:Page/posts` - **23 calls** (8% of usage) - **ACTUAL VALUE**

**Problem:** 82% of your API calls are for page information that rarely changes!

## 🎯 Optimization Solutions Implemented

### 1. **Intelligent Caching System**
```python
# New optimized extractor caches page info for 24 hours
# Reduces page info calls from 156 to ~10 per day
```

**Benefits:**
- ✅ Reduces page info calls by 90%
- ✅ Persistent cache across runs
- ✅ Automatic cache invalidation

### 2. **Priority-Based Processing**
```python
# Process only top 15 pages per run instead of all 87
# Focus on high-activity government pages
```

**Benefits:**
- ✅ Stays within rate limits
- ✅ Focuses on important pages
- ✅ Adaptive priority based on activity

### 3. **Batch Processing**
```python
# Batch database operations
# Minimize API calls for low-engagement posts
```

**Benefits:**
- ✅ Faster database operations
- ✅ Skip detailed extraction for inactive posts
- ✅ Intelligent engagement thresholds

## 🚀 Usage Instructions

### **Use Optimized Version:**
```bash
# Instead of the original scraper
python run_facebook_scraper_optimized.py

# With custom settings
python run_facebook_scraper_optimized.py --max-pages 10 --hours-back 48
```

### **Recommended Settings:**

**For Production (Daily):**
```bash
python run_facebook_scraper_optimized.py --max-pages 15
```

**For Testing:**
```bash
python run_facebook_scraper_optimized.py --max-pages 5 --verbose
```

**For High-Activity Periods:**
```bash
python run_facebook_scraper_optimized.py --max-pages 20 --hours-back 12
```

## 📈 Expected Improvements

### **API Call Reduction:**
- **Before:** 289 calls for 87 pages (3.3 calls/page)
- **After:** ~50 calls for 15 pages (3.3 calls/page, but focused)
- **Cache Effect:** Subsequent runs: ~20 calls for 15 pages (1.3 calls/page)

### **Rate Limit Efficiency:**
- **Day 1:** ~80% reduction in API calls
- **Day 2+:** ~90% reduction due to caching
- **Focus:** Process most important pages reliably

## 🔧 Configuration Options

### **Page Priorities**
The system automatically learns which pages are active and prioritizes them:

```json
{
  "271178572940207": 10,  // Présidence de la République (highest)
  "213636118651883": 10,  // Présidence du Gouvernement
  "1515094915436499": 9,  // Parlement
  "292899070774121": 8    // Ministère de la Justice
}
```

### **Rate Limit Settings**
```python
# In facebook_extractor_optimized.py
self.max_pages_per_run = 15    # Conservative limit
self.min_delay = 0.5           # Delay between API calls
```

## 📊 Monitoring & Analytics

### **View Optimization Results:**
```bash
python run_facebook_scraper_optimized.py --show-recommendations
```

### **Key Metrics to Monitor:**
- **API calls per source** (target: <2.0)
- **Cache hit rate** (target: >80% after day 1)
- **Posts found per API call** (efficiency metric)

### **Log Files:**
- `facebook_scraper_optimized.log` - Detailed optimization logs
- `facebook_page_cache.pkl` - Page information cache
- `facebook_page_priorities.json` - Dynamic page priorities

## 🕐 Recommended Scheduling

### **Option 1: Conservative (Recommended)**
```bash
# Every 6 hours, 15 pages each time
0 */6 * * * python run_facebook_scraper_optimized.py --max-pages 15
```

### **Option 2: Frequent Updates**
```bash
# Every 3 hours, 10 pages each time
0 */3 * * * python run_facebook_scraper_optimized.py --max-pages 10
```

### **Option 3: Peak Hours Focus**
```bash
# Business hours: more pages, off-hours: fewer pages
0 9,12,15,18 * * * python run_facebook_scraper_optimized.py --max-pages 20
0 0,6 * * * python run_facebook_scraper_optimized.py --max-pages 5
```

## 🎯 Advanced Optimizations

### **1. Staggered Processing**
Process different page groups at different times:
```bash
# Morning: Government institutions
# Afternoon: Ministries  
# Evening: Regional governments
```

### **2. Activity-Based Scheduling**
- High-priority pages: Every 3 hours
- Medium-priority pages: Every 6 hours  
- Low-priority pages: Once daily

### **3. Content-Aware Processing**
- Skip detailed extraction for posts with no engagement
- Focus on posts with reactions/comments
- Limit comment extraction for high-volume posts

## 🔍 Troubleshooting

### **If Still Hitting Rate Limits:**
1. Reduce `--max-pages` to 10 or lower
2. Increase delay between calls in extractor
3. Run less frequently (every 8-12 hours)

### **If Missing Important Posts:**
1. Check page priorities in `facebook_page_priorities.json`
2. Manually set high priority for important pages
3. Increase `--hours-back` parameter

### **If Cache Issues:**
1. Delete `facebook_page_cache.pkl` to reset cache
2. Check file permissions
3. Monitor cache hit rates in logs

## 📋 Migration Checklist

- [ ] Test optimized version: `python run_facebook_scraper_optimized.py --max-pages 5`
- [ ] Verify cache creation: Check for `.pkl` and `.json` files
- [ ] Monitor API usage in Meta dashboard
- [ ] Update cron jobs to use optimized version
- [ ] Set up log monitoring for optimization metrics
- [ ] Adjust `max-pages` based on your rate limit comfort zone

## 🎉 Expected Results

After implementing these optimizations:

- **90% reduction** in redundant API calls
- **Reliable processing** of top-priority pages
- **Adaptive learning** of page activity patterns
- **Sustainable rate limit usage** for long-term operation
- **Better data quality** by focusing on active pages

The system will now work within Facebook's rate limits while still capturing the most important government communications from Tunisia! 🇹🇳
