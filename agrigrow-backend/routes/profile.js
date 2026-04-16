// routes/profile.js — Get and update user profile
const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const { dbRun, dbGet, dbAll } = require('../db/database');

const TASK_LABELS = {
  t1: { text: 'Complete one learning lesson', pts: 50 },
  t2: { text: 'Log a sustainable practice',   pts: 30 },
  t3: { text: 'Post or reply in community',   pts: 20 },
};

// GET /api/profile
router.get('/', auth, async (req, res) => {
  try {
    const user = await dbGet('SELECT * FROM users WHERE id = ?', [req.userId]);
    if (!user) return res.status(404).json({ error: 'User not found.' });

    const today = new Date().toISOString().split('T')[0];

    const lessonRows = await dbAll('SELECT lesson_id FROM completed_lessons WHERE user_id = ?', [req.userId]);
    const completedLessons = lessonRows.map(r => r.lesson_id);

    const taskRows = await dbAll('SELECT task_id, done FROM today_tasks WHERE user_id = ? AND date = ?', [req.userId, today]);
    const todayTasks = taskRows.map(r => ({
      id: r.task_id, done: r.done === 1,
      text: TASK_LABELS[r.task_id]?.text || '',
      pts:  TASK_LABELS[r.task_id]?.pts  || 0,
    }));

    const badgeRows = await dbAll('SELECT badge_id, earned FROM badges WHERE user_id = ?', [req.userId]);
    const badges = badgeRows.map(r => ({ id: r.badge_id, earned: r.earned === 1 }));

    const logCount = await dbGet('SELECT COUNT(*) as cnt FROM activity_logs WHERE user_id = ?', [req.userId]);

    res.json({
      user: {
        id: user.id, name: user.name, email: user.email, role: user.role,
        region: user.region, cropType: user.crop_type, farmSize: user.farm_size,
        experience: user.experience, points: user.points, streak: user.streak,
      },
      completedLessons,
      todayTasks,
      badges,
      activityCount: logCount.cnt,
    });
  } catch (err) {
    console.error('Profile get error:', err);
    res.status(500).json({ error: 'Failed to load profile.' });
  }
});

// PUT /api/profile
router.put('/', auth, async (req, res) => {
  try {
    const { name, email, region, cropType, farmSize, experience } = req.body;
    if (!name || !email) return res.status(400).json({ error: 'Name and email are required.' });

    const conflict = await dbGet('SELECT id FROM users WHERE email = ? AND id != ?', [email, req.userId]);
    if (conflict) return res.status(400).json({ error: 'Email already in use.' });

    await dbRun(
      `UPDATE users SET name = ?, email = ?, region = ?, crop_type = ?, farm_size = ?, experience = ? WHERE id = ?`,
      [name, email, region || '', cropType || '', farmSize || '', experience || '', req.userId]
    );

    const user = await dbGet('SELECT * FROM users WHERE id = ?', [req.userId]);
    res.json({
      user: {
        id: user.id, name: user.name, email: user.email, role: user.role,
        region: user.region, cropType: user.crop_type, farmSize: user.farm_size,
        experience: user.experience, points: user.points, streak: user.streak,
      }
    });
  } catch (err) {
    console.error('Profile update error:', err);
    res.status(500).json({ error: 'Failed to update profile.' });
  }
});

module.exports = router;
