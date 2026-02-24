# Affiliate Ops Playbook (Phase B Prep)

This playbook tracks affiliate approvals and launch readiness.

## Priority order (start now)
1. Booking.com Affiliate Partner Program
2. Viator
3. GetYourGuide
4. Eventbrite / ticket partner route
5. OpenTable / restaurant reservation lane

## Application checklist (for each program)
- [ ] Program URL saved
- [ ] Application submitted
- [ ] Approval status logged
- [ ] Tracking link format documented
- [ ] Payout threshold + schedule documented
- [ ] First links deployed on target pages
- [ ] First click recorded in GA4

## Tracking fields
Use `docs/affiliate-program-tracker.csv`:
- program
- submitted_at
- status
- login_url
- tracking_id
- payout_model
- payout_terms
- next_action
- owner

## Page deployment standard
For each approved program:
1. Add links to 3 highest-intent pages in first pass
2. Confirm `rel="nofollow sponsored noopener"`
3. Confirm UTM tags present
4. Confirm event `affiliate_link_click` appears in GA4

## Weekly review cadence
- Monday: status updates + new submissions
- Wednesday: link QA + event QA
- Friday: click report + next-action queue
