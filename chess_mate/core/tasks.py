from celery import shared_task
from typing import Dict, Any, List, Optional
import logging
from .models import Game, Profile
from .game_analyzer import GameAnalyzer
from .cache_manager import CacheManager
from .ai_feedback import AIFeedbackGenerator
from django.db import transaction
from datetime import datetime

logger = logging.getLogger(__name__)
cache_manager = CacheManager()

@shared_task(bind=True, max_retries=3)
def analyze_game_task(self, game_id: int, user_id: int) -> Dict[str, Any]:
    """Analyze a single game asynchronously."""
    try:
        # Check cache first
        cached_analysis = cache_manager.get_cached_analysis(game_id)
        if cached_analysis:
            return cached_analysis

        # Get game and profile
        with transaction.atomic():
            game = Game.objects.get(id=game_id)
            profile = Profile.objects.get(user_id=user_id)
            
            # Verify credits
            if profile.credits < 1:
                raise ValueError("Insufficient credits")
            
            # Deduct credits
            profile.credits -= 1
            profile.save()

        # Perform analysis
        analyzer = GameAnalyzer()
        try:
            analysis_results = analyzer.analyze_games([game])
            game_analysis = analysis_results[game.id]
            
            # Generate AI feedback
            ai_feedback = AIFeedbackGenerator()
            player_profile = {
                'rating': profile.rating,
                'preferred_openings': profile.preferred_openings,
                'recent_performance': profile.recent_performance
            }
            feedback = ai_feedback.generate_personalized_feedback(game_analysis, player_profile)
            
            # Combine results
            results = {
                'analysis': game_analysis,
                'feedback': feedback,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache results
            cache_manager.cache_analysis(game_id, results)
            
            return results
        finally:
            if analyzer:
                analyzer.close_engine()
                
    except Exception as e:
        logger.error(f"Error in analyze_game_task: {str(e)}")
        self.retry(exc=e, countdown=60)  # Retry after 1 minute

@shared_task(bind=True, max_retries=3)
def analyze_batch_games_task(self, game_ids: List[int], user_id: int) -> Dict[str, Any]:
    """Analyze multiple games asynchronously."""
    try:
        results = {
            'individual_games': {},
            'overall_stats': {
                'total_games': len(game_ids),
                'completed': 0,
                'errors': 0
            }
        }
        
        # Get profile and verify credits
        with transaction.atomic():
            profile = Profile.objects.get(user_id=user_id)
            required_credits = len(game_ids)
            
            if profile.credits < required_credits:
                raise ValueError("Insufficient credits")
            
            # Deduct credits
            profile.credits -= required_credits
            profile.save()
        
        analyzer = GameAnalyzer()
        try:
            # Process games in batches
            batch_size = 5
            for i in range(0, len(game_ids), batch_size):
                batch = game_ids[i:i + batch_size]
                games = Game.objects.filter(id__in=batch)
                
                try:
                    # Analyze batch
                    batch_results = analyzer.analyze_games(games)
                    
                    # Process each game in batch
                    for game_id, analysis in batch_results.items():
                        try:
                            # Generate AI feedback
                            ai_feedback = AIFeedbackGenerator()
                            player_profile = {
                                'rating': profile.rating,
                                'preferred_openings': profile.preferred_openings,
                                'recent_performance': profile.recent_performance
                            }
                            feedback = ai_feedback.generate_personalized_feedback(analysis, player_profile)
                            
                            # Store results
                            game_results = {
                                'analysis': analysis,
                                'feedback': feedback,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            results['individual_games'][game_id] = game_results
                            results['overall_stats']['completed'] += 1
                            
                            # Cache individual game results
                            cache_manager.cache_analysis(game_id, game_results)
                            
                        except Exception as e:
                            logger.error(f"Error processing game {game_id}: {str(e)}")
                            results['overall_stats']['errors'] += 1
                            
                except Exception as e:
                    logger.error(f"Error processing batch: {str(e)}")
                    results['overall_stats']['errors'] += len(batch)
                    
        finally:
            if analyzer:
                analyzer.close_engine()
        
        # Calculate overall statistics
        total_mistakes = sum(
            len(game_result['analysis'].get('mistakes', []))
            for game_result in results['individual_games'].values()
        )
        total_blunders = sum(
            len(game_result['analysis'].get('blunders', []))
            for game_result in results['individual_games'].values()
        )
        
        results['overall_stats'].update({
            'average_mistakes': total_mistakes / len(game_ids) if game_ids else 0,
            'average_blunders': total_blunders / len(game_ids) if game_ids else 0,
            'success_rate': (results['overall_stats']['completed'] / len(game_ids)) * 100
        })
        
        return results
        
    except Exception as e:
        logger.error(f"Error in analyze_batch_games_task: {str(e)}")
        self.retry(exc=e, countdown=60)  # Retry after 1 minute

@shared_task
def cleanup_expired_cache_task() -> None:
    """Periodic task to clean up expired cache entries."""
    try:
        cache_manager.clear_all_caches()
    except Exception as e:
        logger.error(f"Error in cleanup_expired_cache_task: {str(e)}")

@shared_task
def update_user_stats_task(user_id: int) -> None:
    """Update user statistics based on analyzed games."""
    try:
        with transaction.atomic():
            profile = Profile.objects.get(user_id=user_id)
            games = Game.objects.filter(player_id=user_id)
            
            total_games = games.count()
            if total_games == 0:
                return
            
            # Calculate statistics
            wins = games.filter(result='win').count()
            losses = games.filter(result='loss').count()
            draws = games.filter(result='draw').count()
            
            # Update profile
            profile.total_games = total_games
            profile.win_rate = (wins / total_games) * 100
            profile.recent_performance = 'improving' if profile.win_rate > 50 else 'stable'
            profile.save()
            
    except Exception as e:
        logger.error(f"Error in update_user_stats_task: {str(e)}") 