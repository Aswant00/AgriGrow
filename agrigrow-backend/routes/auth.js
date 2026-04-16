// routes/auth.js — Register and Login
const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { dbRun, dbGet, initBadgesForUser, initTasksForUser } = require('../db/database');

function generateToken(user) {
  return jwt.sign({ userId: user.id, role: user.role }, process.env.JWT_SECRET, { expiresIn: '7d' });
}

function safeUser(user) {
  return {
    id: user.id, name: user.name, email: user.email, role: user.role,
    region: user.region, cropType: user.crop_type, farmSize: user.farm_size,
    experience: user.experience, points: user.points, streak: user.streak,
  };
}

// POST /api/auth/register
router.post('/register', async (req, res) => {
  try {
    const { name, email, password, region, cropType, farmSize, experience } = req.body;

    if (!name || !email || !password || !region)
      return res.status(400).json({ error: 'Please fill all required fields.' });
    if (password.length < 6)
      return res.status(400).json({ error: 'Password must be at least 6 characters.' });

    const existing = await dbGet('SELECT id FROM users WHERE email = ?', [email]);
    if (existing) return res.status(400).json({ error: 'Email already registered.' });

    const hashed = await bcrypt.hash(password, 10);
    const today = new Date().toISOString().split('T')[0];

    const result = await dbRun(
      `INSERT INTO users (name, email, password, role, region, crop_type, farm_size, experience)
       VALUES (?, ?, ?, 'farmer', ?, ?, ?, ?)`,
      [name, email, hashed, region, cropType || '', farmSize || '', experience || '']
    );

    await initBadgesForUser(result.lastID);
    await initTasksForUser(result.lastID, today);

    const user = await dbGet('SELECT * FROM users WHERE id = ?', [result.lastID]);
    res.status(201).json({ token: generateToken(user), user: safeUser(user) });
  } catch (err) {
    console.error('Register error:', err);
    res.status(500).json({ error: 'Registration failed. Please try again.' });
  }
});

// POST /api/auth/login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password)
      return res.status(400).json({ error: 'Email and password are required.' });

    const user = await dbGet('SELECT * FROM users WHERE email = ?', [email]);
    if (!user) return res.status(401).json({ error: 'Wrong email or password.' });

    const match = await bcrypt.compare(password, user.password);
    if (!match) return res.status(401).json({ error: 'Wrong email or password.' });

    const today = new Date().toISOString().split('T')[0];
    await initTasksForUser(user.id, today);

    res.json({ token: generateToken(user), user: safeUser(user) });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ error: 'Login failed. Please try again.' });
  }
});

module.exports = router;
