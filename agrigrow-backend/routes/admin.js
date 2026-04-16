// routes/admin.js — Admin-only endpoints
const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const { dbRun, dbGet, dbAll, initDb } = require('../db/database');

// ── Admin-only middleware ──────────────────────────────────────────────────────
function adminOnly(req, res, next) {
  if (req.userRole !== 'admin') {
    return res.status(403).json({ error: 'Admin access required.' });
  }
  next();
}

// ── GET /api/admin/stats — Platform analytics ─────────────────────────────────
router.get('/stats', auth, adminOnly, async (req, res) => {
  try {
    const userCount    = await dbGet("SELECT COUNT(*) as cnt FROM users WHERE role != 'admin'");
    const lessonCount  = await dbGet('SELECT COUNT(*) as cnt FROM completed_lessons');
    const practiceCount = await dbGet('SELECT COUNT(*) as cnt FROM activity_logs');
    const badgeCount   = await dbGet("SELECT COUNT(*) as cnt FROM badges WHERE earned = 1");

    res.json({
      users:    userCount.cnt,
      lessons:  lessonCount.cnt,
      practices: practiceCount.cnt,
      badges:   badgeCount.cnt,
    });
  } catch (err) {
    console.error('Admin stats error:', err);
    res.status(500).json({ error: 'Failed to load stats.' });
  }
});

// ── GET /api/admin/users — All registered users ───────────────────────────────
router.get('/users', auth, adminOnly, async (req, res) => {
  try {
    const users = await dbAll(
      `SELECT id, name, email, role, region, crop_type, farm_size, experience, points, streak, created_at
       FROM users ORDER BY created_at DESC`,
      []
    );
    res.json({ users: users.map(u => ({ ...u, cropType: u.crop_type, farmSize: u.farm_size })) });
  } catch (err) {
    console.error('Admin users error:', err);
    res.status(500).json({ error: 'Failed to load users.' });
  }
});

// ── GET /api/admin/users/:id — Full profile of one user ──────────────────────
router.get('/users/:id', auth, adminOnly, async (req, res) => {
  try {
    const userId = parseInt(req.params.id);
    const user = await dbGet('SELECT * FROM users WHERE id = ?', [userId]);
    if (!user) return res.status(404).json({ error: 'User not found.' });

    const completedLessons = await dbAll('SELECT lesson_id, pts, completed_at FROM completed_lessons WHERE user_id = ?', [userId]);
    const badges = await dbAll('SELECT badge_id, earned FROM badges WHERE user_id = ?', [userId]);
    const activityLogs = await dbAll('SELECT practices, date, pts FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10', [userId]);
    const postCount = await dbGet('SELECT COUNT(*) as cnt FROM posts WHERE user_id = ?', [userId]);

    res.json({
      user: {
        id: user.id, name: user.name, email: user.email, role: user.role,
        region: user.region, cropType: user.crop_type, farmSize: user.farm_size,
        experience: user.experience, points: user.points, streak: user.streak,
        createdAt: user.created_at,
      },
      completedLessons: completedLessons.map(l => l.lesson_id),
      badges: badges.map(b => ({ id: b.badge_id, earned: b.earned === 1 })),
      activityLogs: activityLogs.map(l => ({ ...l, practices: JSON.parse(l.practices) })),
      postCount: postCount.cnt,
    });
  } catch (err) {
    console.error('Admin user detail error:', err);
    res.status(500).json({ error: 'Failed to load user details.' });
  }
});

// ── GET /api/admin/modules — Custom modules added by admin ────────────────────
router.get('/modules', auth, adminOnly, async (req, res) => {
  try {
    const modules = await dbAll('SELECT * FROM custom_modules ORDER BY created_at DESC', []);
    res.json({ modules });
  } catch (err) {
    console.error('Admin modules error:', err);
    res.status(500).json({ error: 'Failed to load modules.' });
  }
});

// ── POST /api/admin/modules — Create a new module ────────────────────────────
router.post('/modules', auth, adminOnly, async (req, res) => {
  try {
    const { title, category, difficulty, icon, iconColor, description, duration, expertVerified } = req.body;

    if (!title || !category || !difficulty || !description) {
      return res.status(400).json({ error: 'Title, category, difficulty and description are required.' });
    }

    const result = await dbRun(
      `INSERT INTO custom_modules (title, category, difficulty, icon, icon_color, description, duration, expert_verified, created_by)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [title.trim(), category, difficulty, icon || 'eco', iconColor || '#2e7d32',
       description.trim(), duration || '30 min', expertVerified ? 1 : 0, req.userId]
    );

    const module = await dbGet('SELECT * FROM custom_modules WHERE id = ?', [result.lastID]);
    res.status(201).json({ module });
  } catch (err) {
    console.error('Admin create module error:', err);
    res.status(500).json({ error: 'Failed to create module.' });
  }
});

// ── DELETE /api/admin/modules/:id — Delete a custom module ───────────────────
router.delete('/modules/:id', auth, adminOnly, async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    await dbRun('DELETE FROM custom_modules WHERE id = ?', [id]);
    res.json({ success: true });
  } catch (err) {
    console.error('Admin delete module error:', err);
    res.status(500).json({ error: 'Failed to delete module.' });
  }
});

module.exports = router;
