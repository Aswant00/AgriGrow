// routes/tracker.js — Practice activity logging
const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const { dbRun, dbGet, dbAll } = require('../db/database');

// GET /api/tracker
router.get('/', auth, async (req, res) => {
  try {
    const logs = await dbAll(
      'SELECT id, practices, notes, date, pts, has_proof, created_at FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC',
      [req.userId]
    );
    res.json({
      logs: logs.map(log => ({
        ...log,
        practices: JSON.parse(log.practices),
        hasProof:  log.has_proof === 1,
      }))
    });
  } catch (err) {
    console.error('Tracker get error:', err);
    res.status(500).json({ error: 'Failed to load activity logs.' });
  }
});

// POST /api/tracker
router.post('/', auth, async (req, res) => {
  try {
    const { practices, notes, date, hasProof } = req.body;

    if (!practices || !Array.isArray(practices) || practices.length === 0)
      return res.status(400).json({ error: 'At least one practice must be selected.' });
    if (!date)
      return res.status(400).json({ error: 'Date is required.' });

    const pts = practices.length * 20;

    await dbRun(
      'INSERT INTO activity_logs (user_id, practices, notes, date, pts, has_proof) VALUES (?, ?, ?, ?, ?, ?)',
      [req.userId, JSON.stringify(practices), notes || '', date, pts, hasProof ? 1 : 0]
    );
    await dbRun('UPDATE users SET points = points + ? WHERE id = ?', [pts, req.userId]);

    // Badge b2: water saver (drip irrigation logged 3+ times)
    const waterCount = await dbGet(
      `SELECT COUNT(*) as cnt FROM activity_logs WHERE user_id = ? AND practices LIKE '%"p2"%'`,
      [req.userId]
    );
    if (waterCount.cnt >= 3)
      await dbRun("UPDATE badges SET earned = 1 WHERE user_id = ? AND badge_id = 'b2' AND earned = 0", [req.userId]);

    // Badge b4: 500 points
    const user = await dbGet('SELECT points FROM users WHERE id = ?', [req.userId]);
    if (user.points >= 500)
      await dbRun("UPDATE badges SET earned = 1 WHERE user_id = ? AND badge_id = 'b4' AND earned = 0", [req.userId]);

    // Mark task t2 done
    const today = new Date().toISOString().split('T')[0];
    await dbRun("UPDATE today_tasks SET done = 1 WHERE user_id = ? AND task_id = 't2' AND date = ?", [req.userId, today]);

    const badges = await dbAll('SELECT badge_id, earned FROM badges WHERE user_id = ?', [req.userId]);

    res.status(201).json({
      pts,
      points: user.points,
      badges: badges.map(r => ({ id: r.badge_id, earned: r.earned === 1 })),
    });
  } catch (err) {
    console.error('Tracker post error:', err);
    res.status(500).json({ error: 'Failed to save activity log.' });
  }
});

module.exports = router;
