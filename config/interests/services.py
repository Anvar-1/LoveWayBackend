from django.db.models import Q, Case, When, Value, IntegerField
from config.user.models import User
from config.profiles.models import Profile
from .models import Interest, UserInterest, SearchHistory


class InterestService:
    @staticmethod
    def save_search(user, query, ip_address=None):
        return SearchHistory.objects.create(
            user=user,
            query=query,
            ip_address=ip_address,
        )

    @staticmethod
    def add_interest(user, interest_name, score=1):
        interest_name = interest_name.strip().lower()
        if not interest_name:
            return None

        interest, _ = Interest.objects.get_or_create(name=interest_name)

        user_interest, created = UserInterest.objects.get_or_create(
            user=user,
            interest=interest,
            defaults={"score": score},
        )

        if not created:
            user_interest.score += score
            user_interest.save(update_fields=["score", "updated_at"])

        return user_interest

    @staticmethod
    def process_search(user, query, ip_address=None):
        query = query.strip()
        if not query:
            return

        # search history ga yoziladi
        InterestService.save_search(user, query, ip_address=ip_address)

        # query bo‘linadi va har biri interest sifatida qo‘shiladi
        parts = [part.strip().lower() for part in query.split() if part.strip()]
        for part in parts:
            InterestService.add_interest(user, part, score=1)

    @staticmethod
    def find_related_profiles(query, current_user=None, limit=10):
        query = query.strip().lower()
        if not query:
            return Profile.objects.none()

        qs = (
            Profile.objects
            .select_related("user")
            .filter(
                Q(username__icontains=query) |
                Q(full_name__icontains=query) |
                Q(bio__icontains=query) |
                Q(city__icontains=query) |
                Q(country__icontains=query)
            )
            .annotate(
                score=Case(
                    When(username__iexact=query, then=Value(100)),
                    When(full_name__iexact=query, then=Value(95)),
                    When(username__istartswith=query, then=Value(85)),
                    When(full_name__istartswith=query, then=Value(80)),
                    When(username__icontains=query, then=Value(70)),
                    When(full_name__icontains=query, then=Value(65)),
                    When(bio__icontains=query, then=Value(50)),
                    When(city__icontains=query, then=Value(45)),
                    When(country__icontains=query, then=Value(40)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
            .order_by("-score", "-id")
        )

        if current_user:
            qs = qs.exclude(user=current_user)

        return qs[:limit]



class UserSearchService:
    @staticmethod
    def search(user, query: str):
        query = query.strip()
        if not query:
            return User.objects.none()

        parts = [part.strip() for part in query.split() if part.strip()]

        filters = Q()
        for part in parts:
            filters &= (
                Q(profile__username__icontains=part) |
                Q(profile__full_name__icontains=part)
            )

        users = (
            User.objects
            .select_related("profile")
            .filter(filters)
            .exclude(id=user.id)
            .annotate(
                score=Case(
                    When(profile__username__iexact=query, then=Value(100)),
                    When(profile__full_name__iexact=query, then=Value(95)),
                    When(profile__username__istartswith=query, then=Value(85)),
                    When(profile__full_name__istartswith=query, then=Value(80)),
                    When(profile__username__icontains=query, then=Value(70)),
                    When(profile__full_name__icontains=query, then=Value(65)),
                    default=Value(50),
                    output_field=IntegerField(),
                )
            )
            .order_by("-score", "-id")
            .distinct()[:20]
        )

        return users

    @staticmethod
    def save_history(user, query, ip):
        query = query.strip()
        if not query:
            return None

        return SearchHistory.objects.create(
            user=user,
            query=query,
            ip_address=ip,
        )

    @staticmethod
    def suggest(user):
        # 1) avval userning eng kuchli interestlarini olamiz
        interests = (
            UserInterest.objects
            .filter(user=user)
            .select_related("interest")
            .order_by("-score", "-updated_at")[:5]
        )

        interest_names = [item.interest.name for item in interests if item.interest.name]

        # 2) agar interest bo'lmasa, recent query larni olamiz
        if not interest_names:
            recent_queries = list(
                SearchHistory.objects
                .filter(user=user)
                .order_by("-created_at")
                .values_list("query", flat=True)[:5]
            )

            for q in recent_queries:
                interest_names.extend([part.strip().lower() for part in q.split() if part.strip()])

        # duplicate olib tashlaymiz
        interest_names = list(dict.fromkeys(interest_names))

        # 3) hali ham hech narsa bo‘lmasa fallback
        if not interest_names:
            return (
                User.objects
                .select_related("profile")
                .exclude(id=user.id)
                .order_by("-id")[:20]
            )

        filters = Q()
        for name in interest_names:
            filters |= Q(profile__username__icontains=name)
            filters |= Q(profile__full_name__icontains=name)
            filters |= Q(profile__bio__icontains=name)
            filters |= Q(profile__city__icontains=name)
            filters |= Q(profile__country__icontains=name)

        users = (
            User.objects
            .select_related("profile")
            .filter(filters)
            .exclude(id=user.id)
            .annotate(
                score=Case(
                    *[
                        When(profile__username__icontains=name, then=Value(90 - i * 5))
                        for i, name in enumerate(interest_names[:5])
                    ],
                    *[
                        When(profile__full_name__icontains=name, then=Value(85 - i * 5))
                        for i, name in enumerate(interest_names[:5])
                    ],
                    *[
                        When(profile__bio__icontains=name, then=Value(70 - i * 5))
                        for i, name in enumerate(interest_names[:5])
                    ],
                    default=Value(10),
                    output_field=IntegerField(),
                )
            )
            .order_by("-score", "-id")
            .distinct()[:20]
        )

        return users