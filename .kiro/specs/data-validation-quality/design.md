# Design Document

## Overview

This design adds three simple validation functions to the existing taxi receipt extraction system. The validation will be integrated into the core module to check team member names, validate dates are from 2025 or later, and log warnings for high fare amounts over 100,000 KRW.

## Architecture

The validation functionality will be added to the existing `extract_taxi_receipts.core` module as a new validation layer that processes extracted data before returning it to the caller.

### Current Flow
```
Image Input → OpenAI API Call → Raw Data → Return to Caller
```

### New Flow with Validation
```
Image Input → OpenAI API Call → Raw Data → Validation Layer → Validated Data → Return to Caller
```

## Components and Interfaces

### 1. Validation Functions

Three new validation functions will be added to `core.py`:

```python
def _validate_team_member(name: str) -> str:
    """Validate and correct team member names against predefined list."""
    
def _validate_date(paid_at: str) -> None:
    """Validate date is 2025 or later, log warning if not."""
    
def _validate_fare(fare: int) -> None:
    """Log warning if fare exceeds 100,000 KRW."""
```

### 2. Team Member List

A predefined list of team members will be stored as a module-level constant:

```python
TEAM_MEMBERS = [
    "최홍영", "박다혜", "박상현", "김민주", "최윤선", 
    "김익현", "장수현", "이한울", "김호연", "박성진"
]
```

### 3. Main Validation Function

A single validation function will orchestrate all validations:

```python
def _validate_extracted_data(data: Dict) -> Dict:
    """Apply all validations to extracted data."""
```

### 4. Integration Point

The validation will be integrated into the existing `_call_openai()` function right before returning the combined data.

## Data Models

No changes to existing data models. The validation functions will work with the current data structure:

```python
{
    "paid_at": str,  # "YYYY-MM-DD HH:MM" format
    "fare": int,     # Amount in KRW
    "name": str,     # Team member name
    "route": str     # Trip route
}
```

## Error Handling

### Logging Strategy
- Use Python's built-in `logging` module
- Log warnings for validation issues without stopping processing
- Log at WARNING level for date and fare validation issues
- Log at INFO level for team member name corrections

### Error Scenarios
1. **Invalid Date**: Log warning but continue processing
2. **High Fare**: Log warning but continue processing  
3. **Unknown Team Member**: Keep original name, no logging needed
4. **Missing Data**: Validation functions handle None/empty values gracefully

## Testing Strategy

### Unit Tests
- Test each validation function independently
- Test edge cases (empty strings, None values, boundary conditions)
- Test integration with existing extraction flow

### Test Cases
1. **Team Member Validation**:
   - Exact match with predefined team member
   - No match with predefined team members
   - Empty/None name values

2. **Date Validation**:
   - Valid dates from 2025 onwards
   - Invalid dates before 2025
   - Invalid date formats

3. **Fare Validation**:
   - Normal fare amounts (under 100,000 KRW)
   - High fare amounts (over 100,000 KRW)
   - Edge case: exactly 100,000 KRW

### Integration Tests
- Test full extraction flow with validation enabled
- Verify logging output is generated correctly
- Ensure existing functionality remains unchanged