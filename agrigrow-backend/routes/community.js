// routes/community.js — Forum posts, likes, leaderboard
const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const { dbRun, dbGet, dbAll } = require('../db/database');

function formatTime(isoStr) {
  const diff = Date.now() - new Date(isoStr + 'Z').getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins < 1)   return 'Just now';
  if (mins < 60)  return `${mins} minute${mins !== 1 ? 's' : ''} ago`;
  if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  if (days === 1) return 'Yesterday';
  return `${days} days ago`;
}

// GET /api/posts
router.get('/', auth, async (req, res) => {
  try {
    const posts = await dbAll('SELECT * FROM posts ORDER BY created_at DESC', []);
    const likedRows = await dbAll('SELECT post_id FROM post_likes WHERE user_id = ?', [req.userId]);
    const likedSet = new Set(likedRows.map(r => r.post_id));

    res.json({
      posts: posts.map(p => ({
        id: p.id,
        userId: p.user_id,         // ← expose so frontend can show delete button
        author: p.author,
        isExpert: p.is_expert === 1,
        tag: p.tag,
        body: p.body,
        likes: p.likes,
        liked: likedSet.has(p.id),
        time: formatTime(p.created_at),
        reply: p.reply_text ? {
          author:   p.reply_author,
          text:     p.reply_text,
          isExpert: p.reply_is_expert === 1,
        } : null,
      }))
    });
  } catch (err) {
    console.error('Posts get error:', err);
    res.status(500).json({ error: 'Failed to load posts.' });
  }
});

// POST /api/posts
router.post('/', auth, async (req, res) => {
  try {
    const { body, tag } = req.body;
    if (!body || !body.trim()) return res.status(400).json({ error: 'Post body is required.' });

    const user = await dbGet('SELECT name, role FROM users WHERE id = ?', [req.userId]);
    const isExpert = user.role === 'expert' ? 1 : 0;

    const result = await dbRun(
      'INSERT INTO posts (user_id, author, is_expert, tag, body) VALUES (?, ?, ?, ?, ?)',
      [req.userId, user.name, isExpert, tag || 'General', body.trim()]
    );

    await dbRun('UPDATE users SET points = points + 10 WHERE id = ?', [req.userId]);
    await dbRun("UPDATE badges SET earned = 1 WHERE user_id = ? AND badge_id = 'b6' AND earned = 0", [req.userId]);

    const today = new Date().toISOString().split('T')[0];
    await dbRun("UPDATE today_tasks SET done = 1 WHERE user_id = ? AND task_id = 't3' AND date = ?", [req.userId, today]);

    const updatedUser = await dbGet('SELECT points FROM users WHERE id = ?', [req.userId]);
    const badges = await dbAll('SELECT badge_id, earned FROM badges WHERE user_id = ?', [req.userId]);

    res.status(201).json({
      post: {
        id: result.lastID,
        userId: req.userId,        // ← include in response too
        author: user.name, isExpert: isExpert === 1,
        tag: tag || 'General', body: body.trim(), likes: 0,
        liked: false, time: 'Just now', reply: null,
      },
      points: updatedUser.points,
      badges: badges.map(r => ({ id: r.badge_id, earned: r.earned === 1 })),
    });
  } catch (err) {
    console.error('Post create error:', err);
    res.status(500).json({ error: 'Failed to create post.' });
  }
});

// DELETE /api/posts/:id  — only the post owner can delete
router.delete('/:id', auth, async (req, res) => {
  try {
    const postId = parseInt(req.params.id);
    const post = await dbGet('SELECT id, user_id FROM posts WHERE id = ?', [postId]);
    if (!post) return res.status(404).json({ error: 'Post not found.' });
    if (post.user_id !== req.userId) return res.status(403).json({ error: 'You can only delete your own posts.' });

    // Delete likes first (foreign key), then the post
    await dbRun('DELETE FROM post_likes WHERE post_id = ?', [postId]);
    await dbRun('DELETE FROM posts WHERE id = ?', [postId]);

    res.json({ success: true });
  } catch (err) {
    console.error('Delete post error:', err);
    res.status(500).json({ error: 'Failed to delete post.' });
  }
});

// POST /api/posts/:id/like
router.post('/:id/like', auth, async (req, res) => {
  try {
    const postId = parseInt(req.params.id);
    const post = await dbGet('SELECT id, likes FROM posts WHERE id = ?', [postId]);
    if (!post) return res.status(404).json({ error: 'Post not found.' });

    const alreadyLiked = await dbGet('SELECT 1 FROM post_likes WHERE user_id = ? AND post_id = ?', [req.userId, postId]);

    if (alreadyLiked) {
      await dbRun('DELETE FROM post_likes WHERE user_id = ? AND post_id = ?', [req.userId, postId]);
      await dbRun('UPDATE posts SET likes = likes - 1 WHERE id = ?', [postId]);
      res.json({ liked: false, likes: post.likes - 1 });
    } else {
      await dbRun('INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)', [req.userId, postId]);
      await dbRun('UPDATE posts SET likes = likes + 1 WHERE id = ?', [postId]);
      res.json({ liked: true, likes: post.likes + 1 });
    }
  } catch (err) {
    console.error('Like error:', err);
    res.status(500).json({ error: 'Failed to toggle like.' });
  }
});

module.exports = router;

