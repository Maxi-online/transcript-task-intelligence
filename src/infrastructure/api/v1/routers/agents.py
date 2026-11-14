from starlette.concurrency import run_in_threadpool
from src.core.agents.summarization import ProvidersUnavailableError
from fastapi import APIRouter, Depends, status, HTTPException
import httpx
from src.infrastructure.api.v1.dependencies import get_summarizer_agents, get_llm_monitoring
from src.core.interfaces import LLMProvider, LLMMonitoringProvider
from src.infrastructure.api.v1.schemes import SummarizeRequest, SuccessResponse, ErrorResponse
from src.core.agents import SummarizationAgent, SummarizationDTO

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.post(
    "/summarize",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def summarize(
    request: SummarizeRequest,
    llm_monitoring: LLMMonitoringProvider = Depends(get_llm_monitoring),
    summarizers: dict[str, LLMProvider] = Depends(get_summarizer_agents)
):
    try:
        agent = SummarizationAgent(llm_monitoring, summarizers)
        input_data = SummarizationDTO(user_id=request.user_id, text=request.text, tasks=request.tasks)

        try:
            result = await run_in_threadpool(agent.execute, input_data)
            return {
                "status": "success",
                "data": {
                    "summary": result
                }
            }

        except ProvidersUnavailableError:
            raise HTTPException(status_code=503, detail={"status": "error", "error": {"type": "providers_unavailable", "message": "All providers are unavailable"}})

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "status": "error",
                    "error": {
                        "type": "provider_error",
                        "message": f"Error of the AI-Provider Service: {e.response.status_code}",
                        "details": {
                            "provider_status_code": e.response.status_code
                        }
                    }
                }
            )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    "status": "error",
                    "error": {
                        "type": "timeout",
                        "message": 'Timeout links to AI provider'
                    }
                }
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "error": {
                        "type": "value_error",
                        "message": str(e)
                    }
                }
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "error": {
                        "type": "internal_error",
                        "message": 'Error in summarizing',
                        "details": {
                            "exception_type": type(e).__name__
                        }
                    }
                }
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "error": {
                    "type": "input_error",
                    "message": str(e)
                }
            }
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error": {
                    "type": "critical_error",
                    "message": 'Internal server error'
                }
            }
        )
