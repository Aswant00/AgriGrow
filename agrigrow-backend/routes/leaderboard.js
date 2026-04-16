// routes/leaderboard.js — Top users ranked by points
const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const { dbAll } = require('../db/database');

// GET /api/leaderboard
router.get('/', auth, async (req, res) => {
  try {
    const top = await dbAll(
      "SELECT id, name, region, points FROM users WHERE role != 'admin' ORDER BY points DESC LIMIT 20",
      []
    );
    res.json({ leaderboard: top });
  } catch (err) {
    console.error('Leaderboard error:', err);
    res.status(500).json({ error: 'Failed to load leaderboard.' });
  }
});

module.exports = router;
