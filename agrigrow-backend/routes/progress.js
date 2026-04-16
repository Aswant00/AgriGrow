// routes/progress.js — Lesson completion and daily tasks
const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const { dbRun, dbGet, dbAll } = require('../db/database');

async function checkAndAwardBadges(userId) {
  const user = await dbGet('SELECT points FROM users WHERE id = ?', [userId]);
  const lessons = await dbAll('SELECT lesson_id FROM completed_lessons WHERE user_id = ?', [userId]);

  if (lessons.length >= 1)
    await dbRun("UPDATE badges SET earned = 1 WHERE user_id = ? AND badge_id = 'b1' AND earned = 0", [userId]);
  if (user.points >= 500)
    await dbRun("UPDATE badges SET earned = 1 WHERE user_id = ? AND badge_id = 'b4' AND earned = 0", [userId]);
  if (lessons.length >= 6)
    await dbRun("UPDATE badges SET earned = 1 WHERE user_id = ? AND badge_id = 'b5' AND earned = 0", [userId]);
}

// GET /api/progress
router.get('/', auth, async (req, res) => {
  try {
    const user = await dbGet('SELECT points, streak FROM users WHERE id = ?', [req.userId]);
    const lessons = await dbAll('SELECT lesson_id FROM completed_lessons WHERE user_id = ?', [req.userId]);
    const badges  = await dbAll('SELECT badge_id, earned FROM badges WHERE user_id = ?', [req.userId]);

    res.json({
      points: user.points,
      streak: user.streak,
      completedLessons: lessons.map(r => r.lesson_id),
      badges: badges.map(r => ({ id: r.badge_id, earned: r.earned === 1 })),
    });
  } catch (err) {
    console.error('Progress get error:', err);
    res.status(500).json({ error: 'Failed to load progress.' });
  }
});

// POST /api/progress/lesson — Mark lesson complete
router.post('/lesson', auth, async (req, res) => {
  try {
    const { lessonId, pts } = req.body;
    if (!lessonId || pts == null) return res.status(400).json({ error: 'lessonId and pts are required.' });

    const already = await dbGet('SELECT id FROM completed_lessons WHERE user_id = ? AND lesson_id = ?', [req.userId, lessonId]);
    if (already) return res.json({ alreadyDone: true });

    await dbRun('INSERT INTO completed_lessons (user_id, lesson_id, pts) VALUES (?, ?, ?)', [req.userId, lessonId, pts]);
    await dbRun('UPDATE users SET points = points + ? WHERE id = ?', [pts, req.userId]);
    await checkAndAwardBadges(req.userId);

    const today = new Date().toISOString().split('T')[0];
    await dbRun("UPDATE today_tasks SET done = 1 WHERE user_id = ? AND task_id = 't1' AND date = ?", [req.userId, today]);

    const user = await dbGet('SELECT points FROM users WHERE id = ?', [req.userId]);
    const badges = await dbAll('SELECT badge_id, earned FROM badges WHERE user_id = ?', [req.userId]);

    res.json({ points: user.points, badges: badges.map(r => ({ id: r.badge_id, earned: r.earned === 1 })) });
  } catch (err) {
    console.error('Complete lesson error:', err);
    res.status(500).json({ error: 'Failed to save lesson progress.' });
  }
});

// POST /api/progress/task — Toggle daily task
router.post('/task', auth, async (req, res) => {
  try {
    const { taskId } = req.body;
    if (!taskId) return res.status(400).json({ error: 'taskId is required.' });

    const today = new Date().toISOString().split('T')[0];
    const TASK_PTS = { t1: 50, t2: 30, t3: 20 };

    const task = await dbGet('SELECT done FROM today_tasks WHERE user_id = ? AND task_id = ? AND date = ?', [req.userId, taskId, today]);
    if (!task) return res.status(404).json({ error: 'Task not found for today.' });

    const nowDone = task.done === 0 ? 1 : 0;
    const ptsDelta = nowDone ? TASK_PTS[taskId] : -(TASK_PTS[taskId]);

    await dbRun('UPDATE today_tasks SET done = ? WHERE user_id = ? AND task_id = ? AND date = ?', [nowDone, req.userId, taskId, today]);
    await dbRun('UPDATE users SET points = MAX(0, points + ?) WHERE id = ?', [ptsDelta, req.userId]);

    const user = await dbGet('SELECT points FROM users WHERE id = ?', [req.userId]);
    res.json({ done: nowDone === 1, points: user.points });
  } catch (err) {
    console.error('Toggle task error:', err);
    res.status(500).json({ error: 'Failed to update task.' });
  }
});

module.exports = router;
